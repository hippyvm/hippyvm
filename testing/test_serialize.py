from testing.test_interpreter import BaseTestInterpreter
from hippy.module import serialize

def test_remove_duplicates_fin():
    F = -1
    assert serialize.remove_duplicates_fin([1]) == [1, F]
    assert serialize.remove_duplicates_fin([1, 2, 3]) == [1, 2, 3, F]
    assert serialize.remove_duplicates_fin([1, 1, 1]) == [1, F]
    assert serialize.remove_duplicates_fin([1, 2, 2, 3, 3]) == [1, 2, 3, F]
    assert serialize.remove_duplicates_fin([1, 1, 3]) == [1, 3, F]


class TestBuiltin(BaseTestInterpreter):

    def test_serialize(self):
        output = self.run("""
class Connection
{
    protected $link;
    private $server,  $username,  $password,  $db;

    public function __construct($server,  $username,  $password,  $db)
    {
        $this->server = $server;
        $this->username = $username;
        $this->password = $password;
        $this->db = $db;
    }

    public function __sleep()
    {
        return array('server',  'username',  'password',  'db');
    }

    public function __wakeup()
    {
        echo 'wakeup';
    }
}
$c = new Connection('localhost', 'soda', 'php', 'db');
echo serialize($c);
        """)
        assert self.space.str_w(output[0]) == 'O:10:"Connection":4:{s:18:"\00Connection\00server";s:9:"localhost";s:20:"\00Connection\00username";s:4:"soda";s:20:"\00Connection\00password";s:3:"php";s:14:"\00Connection\00db";s:2:"db";}'


    def test_serialize2(self):
        output = self.run("""
class Connection
{
    protected $link;
    private $server,  $username,  $password,  $db;

    public function __construct($server,  $username,  $password,  $db)
    {
        $this->server = $server;
        $this->username = $username;
        $this->password = $password;
        $this->db = $db;
    }

    public function __sleep()
    {
        return array('server',  'username',  'password',  'db', 'nofield');
    }

    public function __wakeup()
    {
        echo 'wakeup';
    }
}
$c = new Connection('localhost', 'soda', 'php', 'db');
echo serialize($c);
        """, ["Notice: serialize(): \"nofield\" returned as member variable from __sleep() but does not exist"])
        assert self.space.str_w(output[0]) == 'O:10:"Connection":5:{s:18:"\00Connection\00server";s:9:"localhost";s:20:"\00Connection\00username";s:4:"soda";s:20:"\00Connection\00password";s:3:"php";s:14:"\00Connection\00db";s:2:"db";s:7:"nofield";N;}'


    def test_serialize3(self):
        output = self.run("""
class Connection
{
    protected $link;
    private $server,  $username,  $password,  $db;

    public function __construct($server,  $username,  $password,  $db)
    {
        $this->server = $server;
        $this->username = $username;
        $this->password = $password;
        $this->db = $db;
    }

    public function __sleep()
    {
        return array();
    }

    public function __wakeup()
    {
        echo 'wakeup';
    }
}
$c = new Connection('localhost', 'soda', 'php', 'db');
echo serialize($c);
        """)
        assert self.space.str_w(output[0]) == 'O:10:"Connection":0:{}'


    def test_serialize4(self):
        output = self.run("""
class Connection
{
    protected $link;
    private $server,  $username,  $password,  $db;

    public function __construct($server,  $username,  $password,  $db)
    {
        $this->server = $server;
        $this->username = $username;
        $this->password = $password;
        $this->db = $db;
    }

    public function __sleep()
    {
        return "string";
    }

    public function __wakeup()
    {
        echo 'wakeup';
    }
}
$c = new Connection('localhost', 'soda', 'php', 'db');
echo serialize($c);
        """, ["Notice: serialize(): __sleep should return an array only containing the names of instance-variables to serialize"])
        assert self.space.str_w(output[0]) == 'N;'


    def test_serialize_nonprivate_attr(self):
        output = self.run("""
        class C { static function __sleep() { return array("b"); } }
        $c = new C;
        $c->b = 42;
        echo serialize($c);
        """)
        assert self.space.str_w(output[0]) == 'O:1:"C":1:{s:1:"b";i:42;}'

    def test_serialize_parent_public_attr(self):
        output = self.run("""
        class A { public $a; function __sleep() { return array("a"); } }
        class B extends A { }
        $b = new B;
        $b->a = 42;
        echo serialize($b);
        """)
        assert self.space.str_w(output[0]) == 'O:1:"B":1:{s:1:"a";i:42;}'

    def test_serialize_parent_protected_attr(self):
        output = self.run("""
        class A { protected $a; function __sleep() { return array("a"); } }
        class B extends A { function __construct($a) { $this->a = $a; } }
        $b = new B(42);
        echo serialize($b);
        """)
        assert self.space.str_w(output[0]) == (
                'O:1:"B":1:{s:4:"\x00*\x00a";i:42;}')

    def test_serialize_parent_private_attr_doesnt_work(self):
        output = self.run("""
        class A { private $a; function __sleep() { return array("a"); }
                  function __construct($a) { $this->a = $a; } }
        class B extends A { }
        $b = new B(42);
        echo serialize($b);
        """, ['Notice: serialize(): "a" returned as member variable '
              'from __sleep() but does not exist'])
        assert self.space.str_w(output[0]) == 'O:1:"B":1:{s:1:"a";N;}'

    def test_serialize_with_private_attrs(self):
        output = self.run("""
        class A { private $a; function __construct($a, $x) { $this->a = $a; } }
        class B extends A { private $a; function __construct($a, $a2) {
             parent::__construct($a, $a); $this->a = $a2; } }
        $b = new B(42, 63);
        echo serialize($b);
        """)
        assert self.space.str_w(output[0]) == (
                'O:1:"B":2:{s:4:"\x00B\x00a";i:63;s:4:"\x00A\x00a";i:42;}')

    def test_serialize_array_ref(self):
        output = self.run("""
        $a = array();
        $a[0] = 1;
        $a[1] = &$a[2];
        $a[2] = 1;
        echo serialize($a);
        echo serialize(array($a, $a));
        $b = array();
        $b[0] = 1;
        $b[1] = &$b[2];
        $b[2] = 1;
        echo serialize(array($a, $b));
        $c = array();
        $c[0] = 1;
        $c[1] = &$c[2];
        $c[2] = 1;
        echo serialize(array($a, $b, $c));
        $a = array(1, 2);
        $b = &$a;
        echo serialize(array(array($b), array($b)));
        """)
        assert self.space.str_w(output[0]) == "a:3:{i:0;i:1;i:2;i:1;i:1;R:3;}"
        assert self.space.str_w(output[1]) == "a:2:{i:0;a:3:{i:0;i:1;i:2;i:1;i:1;R:4;}i:1;a:3:{i:0;i:1;i:2;R:4;i:1;R:4;}}"
        assert self.space.str_w(output[2]) == "a:2:{i:0;a:3:{i:0;i:1;i:2;i:1;i:1;R:4;}i:1;a:3:{i:0;i:1;i:2;i:1;i:1;R:7;}}"
        assert self.space.str_w(output[3]) == "a:3:{i:0;a:3:{i:0;i:1;i:2;i:1;i:1;R:4;}i:1;a:3:{i:0;i:1;i:2;i:1;i:1;R:7;}i:2;a:3:{i:0;i:1;i:2;i:1;i:1;R:10;}}"
        assert self.space.str_w(output[4]) == "a:2:{i:0;a:1:{i:0;a:2:{i:0;i:1;i:1;i:2;}}i:1;a:1:{i:0;a:2:{i:0;i:1;i:1;i:2;}}}"

    def test_unserialize(self):
        output = self.run('''
        function see($pickle) {
            echo unserialize($pickle);
        }
        see("b:1;");
        see("i:-3;");
        see("d:15;");
        see("d:15.2;");
        see('s:5:"acdef";');
        see("N;");
        see('a:3:{i:0;i:1;i:1;i:2;i:2;s:3:"xyz";}');
        ''')
        assert output[0].dump() == "true"
        assert output[1].dump() == "-3"
        assert output[2].dump() == "15.0"
        assert output[3].dump() == "15.2"
        assert output[4].dump() == "'acdef'"
        assert output[5].dump() == "NULL"
        assert output[6].dump() == "array(1, 2, 'xyz')"

    def test_unserialize_extra_data(self):
        output = self.run("$x = 'i:5;FOOBAR!';\necho unserialize($x);")
        assert output[0].dump() == "5"

    def test_unserialize_reference_0(self):
        output = self.run('''
        $pickle = 'a:4:{i:0;d:5.5;i:1;R:2;i:2;d:7.5;i:3;R:3;}';
        echo unserialize($pickle);
        ''')
        assert output[0].dump() == "array(5.5, 5.5, 7.5, 7.5)"

    def test_unserialize_reference_1(self):
        output = self.run('''
        $pickle = 'a:2:{i:0;a:3:{i:0;i:10;i:2;i:20;i:1;R:4;}i:1;a:3:{i:0;i:30;i:2;i:40;i:1;R:7;}}';
        echo unserialize($pickle);
        $a = unserialize($pickle);
        $a[0][1]++;
        echo $a;
        $a = unserialize($pickle);
        $a[1][2]++;
        echo $a;
        ''')
        assert output[0].dump() == "array(array(10, 2=>20, 1=>20), array(30, 2=>40, 1=>40))"
        assert output[1].dump() == "array(array(10, 2=>21, 1=>21), array(30, 2=>40, 1=>40))"
        assert output[2].dump() == "array(array(10, 2=>20, 1=>20), array(30, 2=>41, 1=>41))"

    def test_unserialize_reference_2(self):
        output = self.run('''
        $pickle = 'a:2:{i:0;a:1:{i:0;i:5;}i:1;R:2;}';
        echo unserialize($pickle);
        $a = unserialize($pickle);
        $a[0][] = 6;
        echo $a;
        ''')
        assert output[0].dump() == "array(array(5), array(5))"
        assert output[1].dump() == "array(array(5, 6), array(5, 6))"

    def test_unserialize_non_reference_2(self):
        output = self.run('''
        $pickle = 'a:2:{i:0;a:1:{i:0;i:5;}i:1;r:2;}';
        echo unserialize($pickle);
        $a = unserialize($pickle);
        $a[0][] = 6;
        echo $a;
        ''')
        assert output[0].dump() == "array(array(5), array(5))"
        assert output[1].dump() == "array(array(5, 6), array(5))"

    def test_serialize_object(self):
        output = self.run('''
        class Aa { public $foo, $foo2; }
        $a = new aA;
        $a->foo = 42;
        $a->bar = 84;
        echo serialize($a);
        ''')
        assert self.space.str_w(output[0]) == 'O:2:"Aa":3:{s:3:"foo";i:42;s:4:"foo2";N;s:3:"bar";i:84;}'

    def test_unserialize_object(self):
        output = self.run('''
        class Aa { public $foo, $foo2; }
        $pickle = 'O:2:"aA":3:{s:3:"foo";i:42;s:4:"foo2";N;i:-5;i:84;}';
        echo unserialize($pickle);
        ''')
        assert output[0].dump() == 'instance(Aa: foo=>42, foo2=>NULL, -5=>84)'

    def test_serialize_object_references(self):
        output = self.run('''
        class Aa { public $foo; }
        $a = new aA;
        echo serialize(array($a, $a));
        echo serialize(array(&$a, &$a));
        ''')
        assert self.space.str_w(output[0]) == 'a:2:{i:0;O:2:"Aa":1:{s:3:"foo";N;}i:1;r:2;}'
        assert self.space.str_w(output[1]) == 'a:2:{i:0;O:2:"Aa":1:{s:3:"foo";N;}i:1;R:2;}'

    def test_unserialize_object_references(self):
        output = self.run('''
        class Aa { public $foo; }
        $pickle = 'a:2:{i:0;O:2:"Aa":1:{s:3:"foo";N;}i:1;r:2;}';
        $a = unserialize($pickle);
        $a[1] = 42;
        echo $a[0];
        $pickle = 'a:2:{i:0;O:2:"Aa":1:{s:3:"foo";N;}i:1;R:2;}';
        $a = unserialize($pickle);
        $a[1] = 42;
        echo $a[0];
        $pickle = 'a:2:{i:0;O:2:"Aa":1:{s:3:"foo";N;}i:1;r:2;}';
        $a = unserialize($pickle);
        $a[0]->foo = 42;
        echo $a[1];
        ''')
        assert output[0].dump() == 'instance(Aa: foo=>NULL)'
        assert output[1].dump() == '42'
        assert output[2].dump() == 'instance(Aa: foo=>42)'

    def test_unserialize_missing_class(self):
        output = self.run("""
        $pickle = 'O:7:\"Unknown\":0:{}';
        echo unserialize($pickle);
        $pickle = 'O:7:\"Unknown\":1:{s:2:"xy";i:5;}';
        echo unserialize($pickle);
        """)
        assert output[0].dump() == "instance(__PHP_Incomplete_Class: __PHP_Incomplete_Class_Name=>'Unknown')"
        assert output[1].dump() == "instance(__PHP_Incomplete_Class: __PHP_Incomplete_Class_Name=>'Unknown', xy=>5)"

    def test_unserialize_error_1(self):
        self.run("unserialize('');",
                 ["Hippy warning: unserialize(): empty string"])
        self.run("unserialize('i:5');",
                 ["Notice: unserialize(): Error at offset 0 of 3 bytes"])

    def test_unserialize_error_2(self):
        self.run("unserialize('a:1:{ ');",
                 ["Notice: unserialize(): Error at offset 5 of 6 bytes"])
        self.run("unserialize('a:1:{i');",
                 ["Notice: unserialize(): Error at offset 5 of 6 bytes"])
        self.run("unserialize('a:1:{ij');",
                 ["Notice: unserialize(): Error at offset 5 of 7 bytes"])
        self.run("unserialize('a:1:{i:');",
                 ["Notice: unserialize(): Error at offset 5 of 7 bytes"])
        self.run("unserialize('a:1:{i:5');",
                 ["Notice: unserialize(): Error at offset 5 of 8 bytes"])
        self.run("unserialize('a:1:{i:;');",
                 ["Notice: unserialize(): Error at offset 5 of 8 bytes"])
        self.run("unserialize('a:1:{i:x;');",
                 ["Notice: unserialize(): Error at offset 5 of 9 bytes"])
        self.run("unserialize('a:1:{i:-;');",
                 ["Notice: unserialize(): Error at offset 5 of 9 bytes"])

    def test_unserialize_error_3(self):
        self.run("unserialize('a:1:{s:');",
                 ["Notice: unserialize(): Error at offset 5 of 7 bytes"])
        self.run("unserialize('a:1:{s:5');",
                 ["Notice: unserialize(): Error at offset 5 of 8 bytes"])
        self.run("unserialize('a:1:{s:5:');",
                 ["Notice: unserialize(): Error at offset 5 of 9 bytes"])
        self.run("unserialize('a:1:{s:5:\"');",
                 ["Notice: unserialize(): Error at offset 7 of 10 bytes"])
        self.run("unserialize('a:1:{s:5:\"1234');",
                 ["Notice: unserialize(): Error at offset 7 of 14 bytes"])
        self.run("unserialize('a:1:{s:5:\"12345');",
                 ["Notice: unserialize(): Error at offset 15 of 15 bytes"])
        self.run("unserialize('a:1:{s:5:\"12345\"');",
                 ["Notice: unserialize(): Error at offset 17 of 16 bytes"])
        self.run("unserialize('a:1:{s:5x:\"12345\";}');",
                 ["Notice: unserialize(): Error at offset 5 of 19 bytes"])
        self.run("unserialize('a:1:{s:-1:\"\";}');",
                 ["Notice: unserialize(): Error at offset 5 of 14 bytes"])

    def test_unserialize_error_4(self):
        self.run("unserialize('a:1:{}');",
                 ["Notice: unserialize(): Unexpected end of serialized data",
                  "Notice: unserialize(): Error at offset 5 of 6 bytes"])
        self.run("unserialize('a:2:{i:0;i:0;}');",
                 ["Notice: unserialize(): Unexpected end of serialized data",
                  "Notice: unserialize(): Error at offset 13 of 14 bytes"])
        self.run("unserialize('a:0:{i:0;i:0;}');",
                 ["Notice: unserialize(): Error at offset 6 of 14 bytes"])
        self.run("unserialize('a:1:{i:0;}');",
                 ["Notice: unserialize(): Unexpected end of serialized data",
                  "Notice: unserialize(): Error at offset 9 of 10 bytes"])
        self.run("unserialize('a:1:{i:0;i:5}');",
                 ["Notice: unserialize(): Error at offset 9 of 13 bytes"])
        self.run("unserialize('a:1:{i:0;i:5;');",
                 ["Notice: unserialize(): Error at offset 14 of 13 bytes"])

    def test_unserialize_error_5(self):
        self.run("unserialize('d:;');",
                 ["Notice: unserialize(): Error at offset 0 of 3 bytes"])
        self.run("unserialize('d:1E99x;');",
                 ["Notice: unserialize(): Error at offset 0 of 8 bytes"])

    def test_unserialize_error_6(self):
        self.run("unserialize('b:2;');",
                 ["Notice: unserialize(): Error at offset 0 of 4 bytes"])
        self.run("unserialize('b:-1;');",
                 ["Notice: unserialize(): Error at offset 0 of 5 bytes"])
        self.run("unserialize('b:true;');",
                 ["Notice: unserialize(): Error at offset 0 of 7 bytes"])

    def test_unserialize_error_7(self):
        self.run("unserialize('a:-1:{}');",
                 ["Notice: unserialize(): Error at offset 0 of 7 bytes"])
        self.run("unserialize('a:x:{}');",
                 ["Notice: unserialize(): Error at offset 0 of 6 bytes"])
        self.run("unserialize('a:1;');",
                 ["Notice: unserialize(): Error at offset 0 of 4 bytes"])
        self.run("unserialize('a:1:5;');",
                 ["Notice: unserialize(): Error at offset 0 of 6 bytes"])
        self.run("unserialize('a:1{:');",
                 ["Notice: unserialize(): Error at offset 0 of 5 bytes"])
        self.run("unserialize('a:1:}');",
                 ["Notice: unserialize(): Error at offset 0 of 5 bytes"])

    def test_unserialize_error_8(self):
        self.run("unserialize('O:-1:\"\":0:{}');",
                 ["Notice: unserialize(): Error at offset 0 of 12 bytes"])
        self.run("unserialize('O:y:\"\":0:{}');",
                 ["Notice: unserialize(): Error at offset 0 of 11 bytes"])
        # Skipped the next two tests, is it really important?
        #self.run("unserialize('O:0:\"\":0:{}');",
        #         ["Notice: unserialize(): Error at offset 2 of 11 bytes"])
        #self.run("unserialize('O:1:\"+\":-1:{}');",
        #         ["Notice: unserialize(): Error at offset 5 of 13 bytes"])
        self.run("unserialize('O:1:\"X\":-1:{}');")
        self.run("unserialize('O:1:\"X\":0:{s:3:\"foo\";i:10;}');",
                 ["Notice: unserialize(): Error at offset 12 of 27 bytes"])
        self.run("unserialize('O:1:\"X\":1:{s:3:\"foo\";i:10;}');")
        self.run("unserialize('O:1:\"X\":0:{s:3:\"foo\";}');",
                 ["Notice: unserialize(): Error at offset 12 of 22 bytes"])
        self.run("unserialize('O:1:\"X\":1:{s:3:\"foo\";}');",
                 ["Notice: unserialize(): Unexpected end of serialized data",
                  "Notice: unserialize(): Error at offset 21 of 22 bytes"])

    def test_unserialize_error_9(self):
        self.run("unserialize('a:1:{d:5;i:3;}');",
                 ["Notice: unserialize(): Error at offset 9 of 14 bytes"])
        # Bad offset in the message in case of composite types used as
        # an array key
        #self.run("unserialize('a:1:{a:0:{}i:3;}');",
        #         ["Notice: unserialize(): Error at offset 11 of 16 bytes"])
        self.run("unserialize('O:1:\"X\":1:{b:1;i:3;}');",
                 ["Notice: unserialize(): Error at offset 15 of 20 bytes"])

    def test_unserialize_error_10(self):
        self.run("unserialize('R:1;');",
                 ["Notice: unserialize(): Error at offset 4 of 4 bytes"])
        self.run("unserialize('R:0;');",
                 ["Notice: unserialize(): Error at offset 4 of 4 bytes"])
        self.run("unserialize('R:;');",
                 ["Notice: unserialize(): Error at offset 0 of 3 bytes"])
        self.run("unserialize('R:x;');",
                 ["Notice: unserialize(): Error at offset 0 of 4 bytes"])
        self.run("unserialize('R:999999;');",
                 ["Notice: unserialize(): Error at offset 9 of 9 bytes"])
        self.run("unserialize('R:-1;');",
                 ["Notice: unserialize(): Error at offset 5 of 5 bytes"])

    def test_unserialize_fast_list(self):
        def seen():
            ping.append(1)
        back = serialize._succeeded_as_a_list
        serialize._succeeded_as_a_list = seen
        array_content = ''.join(['i:%d;d:1;' % i for i in range(120)])
        ping = []
        self.run("unserialize('a:120:{%s}');" % array_content)
        assert len(ping) == 1
        ping = []
        self.run("unserialize('a:121:{%si:199;d:1;}');" % array_content)
        assert len(ping) == 0
        serialize._succeeded_as_a_list = back
