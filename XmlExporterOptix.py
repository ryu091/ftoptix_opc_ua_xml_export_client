import traceback
import logging
import asyncio
import functools

from collections import OrderedDict
import xml.etree.ElementTree as Et
import base64
from dataclasses import fields, is_dataclass
from enum import Enum

from asyncua import ua
from asyncua.ua.uatypes import type_string_from_type
from asyncua.common import xmlexporter
from asyncua.ua import object_ids as o_ids
from asyncua.common.ua_utils import get_base_data_type

_logger = logging.getLogger(__name__)

"""
Modified version of XmlExporter from FreeOPCUA

Add Try-Except
"""

class XmlExporter(xmlexporter.XmlExporter):

    def __init__(self, server, export_values: bool = False, progress_callback = ()):
        super().__init__(server, export_values)
        self.progress_callback = progress_callback

    async def build_etree(self, node_list):
        """
        Create an XML etree object from a list of nodes; custom namespace uris are optional
        Namespaces used by nodes are always exported for consistency.
        Args:
            node_list: list of Node objects for export
            uris: list of namespace uri strings

        Returns:
        """
        self.logger.info('Building XML etree')

        await self._add_namespaces(node_list)
        self._add_models_els()  # Insert <Models> section

        # add all nodes in the list to the XML etree
        progress = 0
        for node in node_list:
            try:
                await self.node_to_etree(node)
                self.progress_callback(progress)
                progress = progress + 1
            except Exception as e:
                self.logger.warn("Error building etree for node %s: %s" % (node, e))
                traceback.print_exc()

        # add aliases to the XML etree
        self._add_alias_els()
        
    async def _get_ns_idxs_of_nodes(self, nodes):
        """
        get a list of all indexes used or references by nodes
        """
        idxs = []
        for node in nodes:
            node_idxs = [node.nodeid.NamespaceIndex]
            try:
                node_idxs.append(node.get_browse_name().NamespaceIndex)
            except Exception:
                pass
            try:
                node_idxs.extend(ref.NodeId.NamespaceIndex for ref in await node.get_references())
            except Exception:
                pass
            node_idxs = list(set(node_idxs))  # remove duplicates
            for i in node_idxs:
                if i != 0 and i not in idxs:
                    idxs.append(i)
        return idxs
       
    async def _add_node_common(self, nodetype, node):
        browsename = await node.read_browse_name()
        nodeid = node.nodeid
        parent = await node.get_parent()
        displayname = (await node.read_display_name()).Text

        try:
            desc_obj = await node.read_description()
            desc = desc_obj.Text if desc_obj and desc_obj.Text else None
        except:
            desc = None

        node_el = Et.SubElement(self.etree.getroot(), nodetype)
        node_el.attrib["NodeId"] = self._node_to_string(nodeid)
        node_el.attrib["BrowseName"] = self._bname_to_string(browsename)

        if parent is not None:
            node_class = await node.read_node_class()
            if node_class in (ua.NodeClass.Object, ua.NodeClass.Variable, ua.NodeClass.Method):
                node_el.attrib["ParentNodeId"] = self._node_to_string(parent)

        self._add_sub_el(node_el, 'DisplayName', displayname, {"Locale": "en"})
        self._add_sub_el(node_el, 'Description', desc or "", {"Locale": "en"})

        await self._add_ref_els(node_el, node)
        return node_el

    async def _all_fields_to_etree(self, struct_el, val):
        for field in fields(val):
            _logger.info(f"field name = '{field.name}'")
            if field.name == "Encoding":
                continue
            type_name = type_string_from_type(field.type)
            await self.member_to_etree( struct_el, field.name, ua.NodeId(getattr(ua.ObjectIds, type_name)), getattr(val, field.name) )

    def _add_models_els(self):
        models_el = Et.SubElement(self.etree.getroot(), "Models")
        model_el = Et.SubElement(models_el, "Model", {"ModelUri": "KEPServerEnterprise"})
        Et.SubElement(model_el, "RequiredModel", {"ModelUri": "http://opcfoundation.org/UA/"})
        # Et.SubElement(model_el, "RequiredModel", {
            # "ModelUri": "urn:FTOptix:TagImporter",
            # "Version": "1.0.8.102"
        # })
        # Et.SubElement(model_el, "RequiredModel", {
            # "ModelUri": "urn:FTOptix:OPCUAImporter",
            # "Version": "1.0.8.115"
        # })

    def _add_sub_el(self, parent, tag, text, attrib=None):
        subel = Et.SubElement(parent, tag)
        if attrib:
            for k, v in attrib.items():
                subel.set(k, v)
        if text != "":
            subel.text = str(text)
        return subel
