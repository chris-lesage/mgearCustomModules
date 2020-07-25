"""Component Chain 01 module"""

import pymel.core as pm
from pymel.core import datatypes

from mgear.shifter import component

from mgear import rigbits
from mgear.core import node, applyop, vector
from mgear.core import attribute, transform, primitive

##########################################################
# COMPONENT
##########################################################


class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""

        self.normal = self.guide.blades["blade"].z * -1
        self.binormal = self.guide.blades["blade"].x

        self.isFk = self.settings["mode"] != 1
        self.isIk = self.settings["mode"] != 0
        self.isFkIk = self.settings["mode"] == 2

        self.WIP = self.options["mode"]

        # FK controllers ------------------------------------
        if self.isFk:
            self.fk_npo = []
            self.fk_ctl = []
            self.fk_ref = []
            self.fk_off = []
            t = self.guide.tra["root"]
            self.ik_cns = primitive.addTransform(
                self.root, self.getName("ik_cns"), t)
            parent = self.ik_cns
            tOld = False
            fk_ctl = None
            self.previousTag = self.parentCtlTag
            for i, t in enumerate(transform.getChainTransform(self.guide.apos, self.normal, self.negate)):
                dist = vector.getDistance(self.guide.apos[i], self.guide.apos[i + 1])
                if self.settings["neutralpose"] or not tOld:
                    tnpo = t
                else:
                    tnpo = transform.setMatrixPosition(
                        tOld,
                        transform.getPositionFromMatrix(t))
                if i:
                    tref = transform.setMatrixPosition(
                        tOld,
                        transform.getPositionFromMatrix(t))
                    fk_ref = primitive.addTransform(
                        fk_ctl,
                        self.getName("fk%s_ref" % i),
                        tref)
                    self.fk_ref.append(fk_ref)
                else:
                    tref = t
                fk_off = primitive.addTransform(
                    parent, self.getName("fk%s_off" % i), tref)
                fk_npo = primitive.addTransform(
                    fk_off, self.getName("fk%s_npo" % i), tnpo)
                # ro is rotation offset. Yup. They coded it in radians... 1.5708 rad is 90 deg :\
                fk_ctl = self.addCtl(
                    fk_npo,
                    "fk%s_ctl" % i,
                    t,
                    self.color_fk,
                    "compas",
                    w=dist,
                    po=datatypes.Vector(0, 0, 0),
                    ro=datatypes.Vector(-1.5708,0-1.5708),
                    tp=self.previousTag,
                    )

                # lock vis
                attribute.lockAttribute(fk_ctl, attributes=['v'])
                # set rotateOrder to xzy. "Barrel roll" rotx remains stable. Spread roty stays on plane of hands.
                fk_ctl.rotateOrder.set(3)
                self.fk_off.append(fk_off)
                self.fk_npo.append(fk_npo)
                self.fk_ctl.append(fk_ctl)
                tOld = t
                self.previousTag = fk_ctl

        # IK controllers ------------------------------------
        if self.isIk:

            normal = vector.getTransposedVector(
                self.normal,
                [self.guide.apos[0], self.guide.apos[1]],
                [self.guide.apos[-2], self.guide.apos[-1]])
            t = transform.getTransformLookingAt(self.guide.apos[-2],
                                                self.guide.apos[-1],
                                                normal,
                                                "xy",
                                                self.negate)
            t = transform.setMatrixPosition(t, self.guide.apos[-1])

            self.ik_cns = primitive.addTransform(self.root,
                                                 self.getName("ik_cns"),
                                                 t)
            self.ikcns_ctl = self.addCtl(self.ik_cns,
                                         "ikcns_ctl",
                                         t,
                                         self.color_ik,
                                         "null",
                                         w=self.size,
                                         tp=self.parentCtlTag)
            self.ik_ctl = self.addCtl(self.ikcns_ctl,
                                      "ik_ctl",
                                      t,
                                      self.color_ik,
                                      "cube",
                                      w=self.size * .3,
                                      h=self.size * .3,
                                      d=self.size * .3,
                                      tp=self.ikcns_ctl)
            attribute.setKeyableAttributes(self.ik_ctl, self.t_params)
            attribute.lockAttribute(self.ik_ctl, attributes=['v'])

            v = self.guide.apos[-1] - self.guide.apos[0]
            v = v ^ self.normal
            v.normalize()
            v *= self.size
            v += self.guide.apos[1]
            self.upv_cns = primitive.addTransformFromPos(
                self.root, self.getName("upv_cns"), v)

            self.upv_ctl = self.addCtl(self.upv_cns,
                                       "upv_ctl",
                                       transform.getTransform(self.upv_cns),
                                       self.color_ik,
                                       "diamond",
                                       w=self.size * .1,
                                       tp=self.parentCtlTag)
            attribute.setKeyableAttributes(self.upv_ctl, self.t_params)

            # Chain
            self.chain = primitive.add2DChain(self.root,
                                              self.getName("chain"),
                                              self.guide.apos,
                                              self.normal,
                                              self.negate)
            self.chain[0].attr("visibility").set(self.WIP)

        # Chain of deformers -------------------------------
        self.loc = []
        parent = self.root
        for i, t in enumerate(transform.getChainTransform(self.guide.apos, self.normal, self.negate)):
            loc = primitive.addTransform(parent, self.getName("%s_loc" % i), t)

            self.loc.append(loc)
            self.jnt_pos.append([loc, i, None, False])

    # =====================================================
    # ATTRIBUTES
    # =====================================================
    def addAttributes(self):
        """Create the anim and setupr rig attributes for the component"""

        # Anim -------------------------------------------
        if self.isFkIk:
            self.blend_att = self.addAnimParam("blend", "Fk/Ik Blend", "double", self.settings["blend"], 0, 1)

        if self.isIk:
            self.roll_att = self.addAnimParam(
                "roll", "Roll", "double", 0, -180, 180)

            # Ref
            if self.settings["ikrefarray"]:
                ref_names = self.get_valid_alias_list(
                    self.settings["ikrefarray"].split(","))
                if len(ref_names) > 1:
                    self.ikref_att = self.addAnimEnumParam(
                        "ikref",
                        "Ik Ref",
                        0,
                        ref_names)

    # =====================================================
    # OPERATORS
    # =====================================================
    def addOperators(self):
        """Create operators and set the relations for the component rig

        Apply operators, constraints, expressions to the hierarchy.
        In order to keep the code clean and easier to debug,
        we shouldn't create any new object in this method.

        """

        # Visibilities -------------------------------------
        if self.isFkIk:
            # fk
            fkvis_node = node.createReverseNode(self.blend_att)

            for fk_ctl in self.fk_ctl:
                for shp in fk_ctl.getShapes():
                    pm.connectAttr(fkvis_node + ".outputX",
                                   shp.attr("visibility"))

            # ik
            for shp in self.upv_ctl.getShapes():
                pm.connectAttr(self.blend_att, shp.attr("visibility"))
            for shp in self.ikcns_ctl.getShapes():
                pm.connectAttr(self.blend_att, shp.attr("visibility"))
            for shp in self.ik_ctl.getShapes():
                pm.connectAttr(self.blend_att, shp.attr("visibility"))

        # FK Chain -----------------------------------------
        if self.isFk:
            for off, ref in zip(self.fk_off[1:], self.fk_ref):
                applyop.gear_mulmatrix_op(
                    ref.worldMatrix, off.parentInverseMatrix, off, "rt")
        # IK Chain -----------------------------------------
        if self.isIk:
            self.ikh = primitive.addIkHandle(
                self.root, self.getName("ikh"), self.chain)
            self.ikh.attr("visibility").set(False)

            # Constraint and up vector
            pm.pointConstraint(self.ik_ctl, self.ikh, maintainOffset=False)
            pm.poleVectorConstraint(self.upv_ctl, self.ikh)

            # TwistTest
            o_list = [round(elem, 4) for elem
                      in transform.getTranslation(self.chain[1])] \
                != [round(elem, 4) for elem in self.guide.apos[1]]

            if o_list:
                add_nodeTwist = node.createAddNode(180.0, self.roll_att)
                pm.connectAttr(add_nodeTwist + ".output",
                               self.ikh.attr("twist"))
            else:
                pm.connectAttr(self.roll_att, self.ikh.attr("twist"))

        # Chain of deformers -------------------------------
        if self.settings["mode"] == 0:  # fk only
            # Loop until the last one and connect aim constraints from index+1
            for i, loc in enumerate(self.loc[0:-1]):
                pm.pointConstraint(self.fk_ctl[i], loc, maintainOffset=False)
                pm.connectAttr(self.fk_ctl[i] + ".scale", loc + ".scale")
                pm.aimConstraint(
                        self.fk_ctl[i+1],
                        loc,
                        maintainOffset=False,
                        aimVector=(1,0,0),
                        upVector=(0,1,0),
                        worldUpType='none',
                        )
                oRoot = rigbits.addNPO(loc)[0]
                pm.parentConstraint(self.fk_ctl[i], oRoot, mo=True)
                attribute.lockAttribute(oRoot)
            # Then connect the last in the chain as a parent constraint
            pm.parentConstraint(self.fk_ctl[-1], self.loc[-1], maintainOffset=False)
            pm.connectAttr(self.fk_ctl[-1] + ".scale", self.loc[-1] + ".scale")

    # =====================================================
    # CONNECTOR
    # =====================================================
    def setRelation(self):
        """Set the relation beetween object from guide to rig"""

        self.relatives["root"] = self.loc[0]
        self.controlRelatives["root"] = self.fk_ctl[0]
        self.jointRelatives["root"] = 0
        for i in range(0, len(self.loc) - 1):
            self.relatives["%s_loc" % i] = self.loc[i + 1]
            self.controlRelatives["%s_loc" % i] = self.fk_ctl[i + 1]
            self.jointRelatives["%s_loc" % i] = i + 1
            self.aliasRelatives["%s_ctl" % i] = i + 1
        self.relatives["%s_loc" % (len(self.loc) - 1)] = self.loc[-1]
        self.controlRelatives["%s_loc" % (len(self.loc) - 1)] = self.fk_ctl[-1]
        self.jointRelatives["%s_loc" % (len(self.loc) - 1)] = len(self.loc) - 1
        self.aliasRelatives["%s_loc" % (len(self.loc) - 1)] = len(self.loc) - 1

    # @param self
    def addConnection(self):
        """Add more connection definition to the set"""

        self.connections["standard"] = self.connect_standard
        self.connections["orientation"] = self.connect_orientation
        self.connections["parent"] = self.connect_parent

    def connect_orientation(self):
        """orientation connection definition for the component"""
        self.connect_orientCns()

    def connect_standard(self):
        """standard connection definition for the component"""
        self.connect_standardWithSimpleIkRef()

    def connect_parent(self):
        self.connect_standardWithSimpleIkRef()
