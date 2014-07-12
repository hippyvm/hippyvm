<?

class A {
	function __construct() {
		$this->p = array(1, 2, 3);
	}

	function g() {
		count($this->p);
	}
}

function f() {
	$a = new A();
	for ($i = 0; $i < 1000000; $i++) {
		$a->g();
	}
}

f();

?>