
from testing.test_interpreter import BaseTestInterpreter

class TestXML(BaseTestInterpreter):
    def test_basic_parse(self):
        output = self.run("""
        $parser = xml_parser_create();
        $x = "";

        function callback($parser, $arg) {
             global $x;
             $x .= $arg;
        }
        
		xml_set_character_data_handler($parser, 'callback');
        xml_parse($parser, "<a>&lt;b&gt;c&lt;/b&gt;</a>", true);
        echo $x;
        """)
        assert self.unwrap(output[0]) == "<b>c</b>"
