from testing.test_interpreter import BaseTestInterpreter
import pytest


class TestArray(BaseTestInterpreter):

    def test_md2(self):
        output = self.run('''
        echo hash("md2", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "0c486bdcb26ab27500a3b9430551e230"

    def test_md4(self):
        output = self.run('''
        echo hash("md4", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "765b066d927c8e234164f014d3afcf87"

    def test_md5(self):
        output = self.run('''
        echo hash("md5", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "e1bfd762321e409cee4ac0b6e841963c"

    def test_sha1(self):
        output = self.run('''
        echo hash("sha1", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "47425e4490d1548713efea3b8a6f5d778e4b1766"

    def test_sha224(self):
        output = self.run('''
        echo hash("sha224", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "b62baeb0f0fdbc2341908ae75b84446c698dd847c0526693869605d2"

    def test_sha256(self):
        output = self.run('''
        echo hash("sha256", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "12a5d18ee896e59954bdce0f4acc7212eebe03dae1834ef4ce160ac5afa5c4a8"

    def test_sha384(self):
        output = self.run('''
        echo hash("sha384", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "7ecc1178406415a12747674afe7b57424731a4b476f0bab701ebbb15d31233bc1434d83c283a1cc40bc479e1e63ca046"

    def test_sha512(self):
        output = self.run('''
        echo hash("sha512", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "146179738dd42a9eafe5d2740bdf36d584d38d5f42e6fede12e828d5bf97a57a180bfa90c157c173e09a5c71876695807c06d39985c4ddf7b7d9800cb84ab9d7"

    def test_ripemd128(self):
        output = self.run('''
        echo hash("ripemd128", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "5b9a0b079b5abd97e8e3dfea15012213"

    def test_ripemd160(self):
        output = self.run('''
        echo hash("ripemd160", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "c78245cd5ed139bac66a99cb94afe97661eb8a3f"

    def test_ripemd256(self):
        output = self.run('''
        echo hash("ripemd256", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "8fdcc792f25ba6bcda5125a94e2ea5013e9ffd48141e843452da7d3f7fc36d23"

    def test_ripemd320(self):
        output = self.run('''
        echo hash("ripemd320", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "050331efe71e6514b6ed8bea97cf5225f1c642b4cbef7e5091ddb35ec4602b905599eeda86e6b8b2"

    def test_whirlpool(self):
        output = self.run('''
        echo hash("whirlpool", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "ccfc01f76cea38fa16f045f5c1697d857eb938892b34ef5e2233548a5a1211d807dd8d7bc56e8facd9aa4a4921641c444505b65b0772ac73be937db0910d945e"

    def test_tiger128_3(self):
        output = self.run('''
        echo hash("tiger128,3", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "f8f4e87befd50e044ad21f78aac71726"

    def test_tiger160_3(self):
        output = self.run('''
        echo hash("tiger160,3", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "f8f4e87befd50e044ad21f78aac717262a0adbed"

    def test_tiger192_3(self):
        output = self.run('''
        echo hash("tiger192,3", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "f8f4e87befd50e044ad21f78aac717262a0adbed86dc6772"

    def test_tiger128_4(self):
        output = self.run('''
        echo hash("tiger128,4", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "1c2703aed137786154befc6868da46bc"

    def test_tiger160_4(self):
        output = self.run('''
        echo hash("tiger160,4", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "1c2703aed137786154befc6868da46bc9f5dcbb2"

    def test_tiger192_4(self):
        output = self.run('''
        echo hash("tiger192,4", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "1c2703aed137786154befc6868da46bc9f5dcbb28198dc31"

    def test_snefru(self):
        output = self.run('''
        echo hash("snefru", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "bae6ce42009e5ee7c1e9294d21efc9790bcb80a9953bad3e629e5c597b0638a1"

    def test_snefru256(self):
        output = self.run('''
        echo hash("snefru256", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "bae6ce42009e5ee7c1e9294d21efc9790bcb80a9953bad3e629e5c597b0638a1"

    def test_gost(self):
        output = self.run('''
        echo hash("gost", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "ed8039b2a8b81b44f7903b55d51dc9dda1af2529ee4647ad90046cb0d68e4ace"

    def test_adler32(self):
        output = self.run('''
        echo hash("adler32", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "02930149"

    def test_crc32(self):
        output = self.run('''
        echo hash("crc32", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "70ff3613"

    def test_crc32b(self):
        output = self.run('''
        echo hash("crc32b", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "569121d1"

    def test_fnv132(self):
        output = self.run('''
        echo hash("fnv132", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "43775e3f"

    def test_fnv164(self):
        output = self.run('''
        echo hash("fnv164", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "d8a9ca186b84547f"

    def test_joaat(self):
        output = self.run('''
        echo hash("joaat", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "b1e186c8"

    def test_haval128_3(self):
        output = self.run('''
        echo hash("haval128,3", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "7b1e887549ba960e9a0dfdade24ac1df"

    def test_haval160_3(self):
        output = self.run('''
        echo hash("haval160,3", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "4155833e9234a40858e377d0a7034f388774f742"

    def test_haval192_3(self):
        output = self.run('''
        echo hash("haval192,3", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "a6538a66c878c8c2790d93ed3bae5095d0b1aa9cfbec7f39"

    def test_haval224_3(self):
        output = self.run('''
        echo hash("haval224,3", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "b58a5076078a812afc8ef6266faa41300f6c90ae90a6c7d89dc2fec3"

    def test_haval256_3(self):
        output = self.run('''
        echo hash("haval256,3", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "a74b42d01eb6bccf218415f16144ee57f04f44555b4f947f7c97bc4224aba62e"

    def test_haval128_4(self):
        output = self.run('''
        echo hash("haval128,4", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "cb3eeb48e51dadf6c4ebe6a5a6e3981e"

    def test_haval160_4(self):
        output = self.run('''
        echo hash("haval160,4", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "49ba3a12be36735856dd6bf590512968e02190db"

    def test_haval192_4(self):
        output = self.run('''
        echo hash("haval192,4", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "e76c8953c9fb4f2ea95533665050c160caa964a85ad5d880"

    def test_haval224_4(self):
        output = self.run('''
        echo hash("haval224,4", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "e56d724fde10d1c30ab2031843f374d14323b57aa9001780c6e0bc5a"

    def test_haval256_4(self):
        output = self.run('''
        echo hash("haval256,4", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "b4ce192d464cbac646fc5ea834d1518d1b96e5b704a2c38c47065286e584ad79"

    def test_haval128_5(self):
        output = self.run('''
        echo hash("haval128,5", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "32e4cc681d7499f7df1e61c0470b79bf"

    def test_haval160_5(self):
        output = self.run('''
        echo hash("haval160,5", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "4e3f1e83c100db4857cc141d1f1ada68d6f4b588"

    def test_haval192_5(self):
        output = self.run('''
        echo hash("haval192,5", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "586e134724506783724e9f690fa05c35cd2472272b6250fe"

    def test_haval224_5(self):
        output = self.run('''
        echo hash("haval224,5", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "0e70ba3ba5651b906ad92ffcf80745f88d181eeabfe9481b4e3c77b0"

    def test_haval256_5(self):
        output = self.run('''
        echo hash("haval256,5", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "7f5c091f50d1b4948c8f23121f41d795cd2d14f802c8f1a09664333b8b890b98"

    def test_raw_md2(self):
        import md5
        output = self.run('''
        echo hash("md2", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "40f5ce306cba15d1256182f620b3fdd1"

    def test_raw_md4(self):
        import md5
        output = self.run('''
        echo hash("md4", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "adc24d0e0eb0a8b26f21f9a1b95f361d"

    def test_raw_md5(self):
        import md5
        output = self.run('''
        echo hash("md5", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "e62e824131574bc7a294c8b39b014d4a"

    def test_raw_sha1(self):
        import md5
        output = self.run('''
        echo hash("sha1", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "c409c0762e20b61fca8a5661415495b8"

    def test_raw_sha224(self):
        import md5
        output = self.run('''
        echo hash("sha224", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "bc8f445f2c6e8aa8a5bb89a93a8e8350"

    def test_raw_sha256(self):
        import md5
        output = self.run('''
        echo hash("sha256", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "1e8fa266b5f865c7af37cdb282ddbe3e"

    def test_raw_sha384(self):
        import md5
        output = self.run('''
        echo hash("sha384", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "6050d50d373918261786c4f1c76ac7c7"

    def test_raw_sha512(self):
        import md5
        output = self.run('''
        echo hash("sha512", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "986cc253fa4aa169e17b0cfbd665cdf8"

    def test_raw_ripemd128(self):
        import md5
        output = self.run('''
        echo hash("ripemd128", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "acdd2aad79a7bcac805d5337f2cd35bd"

    def test_raw_ripemd160(self):
        import md5
        output = self.run('''
        echo hash("ripemd160", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "3d38785a7bfcd1e1db75e405b8f1306a"

    def test_raw_ripemd256(self):
        import md5
        output = self.run('''
        echo hash("ripemd256", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "863981d5498801af945d6190b0917ef8"

    def test_raw_ripemd320(self):
        import md5
        output = self.run('''
        echo hash("ripemd320", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "f3d561cb6341bcf757281f53a59f180a"

    def test_raw_whirlpool(self):
        import md5
        output = self.run('''
        echo hash("whirlpool", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "283fe7911095bd756cc906aabe775ba6"

    def test_raw_tiger128_3(self):
        import md5
        output = self.run('''
        echo hash("tiger128,3", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "7d63dd40ff0200141d4a69b4ff930114"

    def test_raw_tiger160_3(self):
        import md5
        output = self.run('''
        echo hash("tiger160,3", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "73be9e8d36fd5ff2e353857981ec4b78"

    def test_raw_tiger192_3(self):
        import md5
        output = self.run('''
        echo hash("tiger192,3", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "ff23845c8f60bb75a98d3dca436e707b"

    def test_raw_tiger128_4(self):
        import md5
        output = self.run('''
        echo hash("tiger128,4", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "c42a8cab92fc867699224ed093b6306e"

    def test_raw_tiger160_4(self):
        import md5
        output = self.run('''
        echo hash("tiger160,4", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "ec4c4a5c28831b6779d89d032f4e6cfa"

    def test_raw_tiger192_4(self):
        import md5
        output = self.run('''
        echo hash("tiger192,4", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "063af2a4356b5923b67282889677be54"

    def test_raw_snefru(self):
        import md5
        output = self.run('''
        echo hash("snefru", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "d8e633280559c1ef3c599d1f3a65c705"

    def test_raw_snefru256(self):
        import md5
        output = self.run('''
        echo hash("snefru256", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "d8e633280559c1ef3c599d1f3a65c705"

    def test_raw_gost(self):
        import md5
        output = self.run('''
        echo hash("gost", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "b705d06553558fc96e88d7ff5617801c"

    def test_raw_adler32(self):
        import md5
        output = self.run('''
        echo hash("adler32", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "7a429283defc2ccb629bdef40d0c8cc1"

    def test_raw_crc32(self):
        import md5
        output = self.run('''
        echo hash("crc32", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "3c220b09edf64e4fe846f3d71f5906cb"

    def test_raw_crc32b(self):
        import md5
        output = self.run('''
        echo hash("crc32b", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "3bd5fb0055bb0973a2d96a6db810bfde"

    def test_raw_fnv132(self):
        import md5
        output = self.run('''
        echo hash("fnv132", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "a967f2a52f4eefd087378623d61072e0"

    def test_raw_fnv164(self):
        import md5
        output = self.run('''
        echo hash("fnv164", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "7f79ae6a90e6a12feb4c481741e9073f"

    def test_raw_joaat(self):
        import md5
        output = self.run('''
        echo hash("joaat", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "f1fc17fb616cc24a0faaeaf82c545f07"

    def test_raw_haval128_3(self):
        import md5
        output = self.run('''
        echo hash("haval128,3", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "151ad1a9bd18adc7feb3371d3d340ecf"

    def test_raw_haval160_3(self):
        import md5
        output = self.run('''
        echo hash("haval160,3", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "5329b3cf6b631dd588ff2f78df6acc0e"

    def test_raw_haval192_3(self):
        import md5
        output = self.run('''
        echo hash("haval192,3", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "dcf654cdb175c5a6bd959618e2347053"

    def test_raw_haval224_3(self):
        import md5
        output = self.run('''
        echo hash("haval224,3", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "c60a340ca3e74dcf086fc77583ed2233"

    def test_raw_haval256_3(self):
        import md5
        output = self.run('''
        echo hash("haval256,3", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "9c39f5961dcd02fb2ae993bc51aedd42"

    def test_raw_haval128_4(self):
        import md5
        output = self.run('''
        echo hash("haval128,4", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "da5d36509b00852d607be559ba44d968"

    def test_raw_haval160_4(self):
        import md5
        output = self.run('''
        echo hash("haval160,4", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "f73214863b3520dfd3060aed083fe068"

    def test_raw_haval192_4(self):
        import md5
        output = self.run('''
        echo hash("haval192,4", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "57de554aa22a8e8abd1662e18de219b5"

    def test_raw_haval224_4(self):
        import md5
        output = self.run('''
        echo hash("haval224,4", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "9be92af3727d8d1f4c4402c1a5fe5a9b"

    def test_raw_haval256_4(self):
        import md5
        output = self.run('''
        echo hash("haval256,4", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "8bd8017f638f7cf49da010d72fee5569"

    def test_raw_haval128_5(self):
        import md5
        output = self.run('''
        echo hash("haval128,5", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "10fcf5dd6babefbf19e61db412e1ea53"

    def test_raw_haval160_5(self):
        import md5
        output = self.run('''
        echo hash("haval160,5", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "c67314a46666d06e7521d0564cc1ec0a"

    def test_raw_haval192_5(self):
        import md5
        output = self.run('''
        echo hash("haval192,5", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "ee212b74620ac4ef74848de0a2b54567"

    def test_raw_haval224_5(self):
        import md5
        output = self.run('''
        echo hash("haval224,5", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "93647955087942cf227a53eb43a81026"

    def test_raw_haval256_5(self):
        import md5
        output = self.run('''
        echo hash("haval256,5", "php", 1);
        ''')
        space = self.space
        s = space.str_w(output[0])
        assert md5.new(s).hexdigest() == "96eae5ce76b317c20a75e8b821361c1e"

    def test_hmac_md5(self):
        output = self.run('''
        echo hash_hmac("md5", "php", "php");
        ''')
        space = self.space
        assert space.str_w(output[0]) == "720f7625c909264cf7c38921852d695b"

    def test_hash_init_with_hmac(self):
        output = self.run('''
        $ctx = hash_init('md5',HASH_HMAC,str_repeat(chr(0x0b), 16));
        hash_update($ctx, 'Hi There');
        echo hash_final($ctx);
        ''')
        space = self.space
        assert space.str_w(output[0]) == "9294727a3638bb1c13f48ef8158bfc9d"
