--TEST--
The same rules are applied for properties that are defined in the class hierarchy. Thus, if the properties are compatible, a notice is issued, if not a fatal error occures. (relevant with #60536)
--FILE--
<?php
error_reporting(E_ALL | E_STRICT);

class Base {
  private $hello;    
}

trait THello1 {
  private $hello;
}

echo "PRE-CLASS-GUARD\n";
class Notice extends Base {
    use THello1;
    private $hello;
}
echo "POST-CLASS-GUARD\n";

// now we do the test for a fatal error

class TraitsTest {
	use THello1;
    public $hello;
}

echo "POST-CLASS-GUARD2\n";

$t = new TraitsTest;
$t->hello = "foo";
?>
--EXPECTF--	
PRE-CLASS-GUARD

Strict Standards: Notice and THello1 define the same property ($hello) in the composition of Notice. This might be incompatible, to improve maintainability consider using accessor methods in traits instead. Class was composed in %s on line %d
POST-CLASS-GUARD

Fatal error: TraitsTest and THello1 define the same property ($hello) in the composition of TraitsTest. However, the definition differs and is considered incompatible. Class was composed in %s on line %d
