class MockRpc:
    def validateaddress(self, address):
        data = {"account": "reddit-just-an-dev", "ismine": 'true', "isvalid": 'true', "iscompressed": 'true',
                "isscript": 'false', "iswatchonly": 'false', "address": "nnz4zsVZtpngPVmARnvzBS79DwV6k7vRvS",
                "pubkey": "02cacc9e6cfcbb0b2a23569838ad908193a9a1456911fe45c4fff7f9daa06b8809",
                "scriptPubKey": "76a914ce2100bf6580b586dba3c0d2df0f2196940d2f4588ac"}
        return data

    def getnewaddress(self, account=None):
        data = "nnBKn39onxAuS1cr6KuLAoV2SdfFh1dpsR"
        return data
