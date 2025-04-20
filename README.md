KEPServerEnterprise OPC UA XML Export client

=========================

<strike>This client exports all nodes from a running OPC UA server into a node XML file</strike>

This client is modified from the original to exports all nodes from a running `KEPServerEnterprise` into a node XML file for `FactoryTalk Optix Studio 1.5.2.13`

Dependencies

---

- Python3
- opcua-asyncio v0.9.98 (https://github.com/FreeOpcUa/opcua-asyncio)
- progressbar2 (https://pypi.org/project/progressbar2/)

Install

---
```bash
git clone https://github.com/ryu091/ftoptix_opc_ua_xml_export_client.git
```
```bash
cd ftoptix_opc_ua_xml_export_client
```
```bash
pip install -r requirements.txt
```

Run

---

Export nodes from server `opc.tcp://localhost:49320` into XML file `export.xml`

```
python NodeXmlExporterOptix.py opc.tcp://localhost:49320 export-ns2-optix.xml

# Export only namespace 2
python NodeXmlExporterOptix.py opc.tcp://localhost:49320 export-ns2-optix.xml --namespace 2

# Export with username/password
python NodeXmlExporterOptix.py opc.tcp://localhost:49320 --namespace 2 -u myusername -p somestrongpassword export-ns2-optix.xml
```
