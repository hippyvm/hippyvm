<?

// Task IDs
define('I_IDLE', 1);
define('I_WORK', 2);
define('I_HANDLERA', 3);
define('I_HANDLERB', 4);
define('I_DEVA', 5);
define('I_DEVB', 6);

// Packet types
define('K_DEV', 1000);
define('K_WORK', 1001);

// Packet

define('BUFSIZE', 4);
$BUFSIZE_RANGE = array(0, 1, 2, 3);

class Packet {
	function __construct($l, $i, $k) {
		$this->link = $l;
		$this->ident = $i;
		$this->kind = $k;
		$this->daturm = 0;
		$this->data = array(0, 0, 0, 0);
	}

	function append_to($lst) {
		$this->link = null;
		if ($lst === null)
			return $this;
		$p = $lst;
		$next = $p->link;
		while ($next !== null) {
			$p = $next;
			$next = $p->link;
		}
		$p->link = $this;
		return $lst;
	}
}

class TaskRec {}

class DeviceTaskRec extends TaskRec {
	function __construct() {
		$this->pending = null;
	}
}

class IdleTaskRec extends TaskRec {
	function __construct() {
		$this->control = 1;
		$this->count = 10000;
	}
}

class HandlerTaskRec extends TaskRec {
    function __construct() {
        $this->work_in = null;
		$this->device_in = null;
	}

	function workInAdd($p) {
		$x = $p->append_to($this->work_in);
		$this->work_in = $x;
		return $x;
	}

	function deviceInAdd($p) {
		$x = $p->append_to($this->device_in);
		$this->device_in = $x;
		return $x;
	}
}

class WorkTaskRec extends TaskRec {
	function __construct() {
		$this->destination = I_HANDLERA;
		$this->count = 0;
	}
}

class TaskState {
	function __construct() {
		$this->packet_pending = true;
		$this->task_waiting = false;
		$this->task_holding = false;
	}

	function packetPending() {
		$this->packet_pending = true;
		$this->task_waiting = false;
		$this->task_holding = false;
		return $this;
	}

	function waiting() {
		$this->packet_pending = false;
		$this->task_waiting = true;
		$this->task_holding = false;
		return $this;
	}

	function running() {
		$this->packet_pending = false;
		$this->task_waiting = false;
		$this->task_holding = false;
		return $this;
	}

	function waitingWithPacket() {
		$this->packet_pending = true;
		$this->task_waiting = true;
		$this->task_holding = false;
		return $this;
	}

	function isPacketPending() {
		return $this->packet_pending;
	}

	function isTaskWaiting() {
		return $this->task_waiting;
	}

	function isTaskHolding() {
		return $this->task_holding;
	}

	function isTaskHoldingOrWaiting() {
		return $this->task_holding || (!$this->packet_pending && $this->task_waiting);
	}

	function isWaitingWithPacket() {
		return $this->packet_pending && $this->task_waiting && !$this->task_holding;
	}
}

define('TASKTABSIZE', 10);

$layout = 0;

function trace($a) {
	global $layout;

	$layout--;
	if ($layout <= 0) {
		printf("\n");
		$layout = 50;
	}
	printf("%s ", $a);
}

class TaskWorkArea {
	function __construct() {
		$this->taskTab = array();
		for ($i = 0; $i < TASKTABSIZE; $i++) {
			$this->taskTab[] = null;
		}
		$this->taskList = null;
		$this->holdCount = 0;
		$this->qpktCount = 0;
	}
}

class Task extends TaskState {
	function __construct($i, $p, $w, $initialState, $r) {
		global $taskWorkArea;

		$this->link = $taskWorkArea->taskList;
		$this->ident = $i;
		$this->priority = $p;
		$this->input = $w;

		$this->packet_pending = $initialState->isPacketPending();
		$this->task_waiting = $initialState->isTaskWaiting();
		$this->task_holding = $initialState->isTaskHolding();

		$this->handle = $r;

		$taskWorkArea->taskList = $this;
		$taskWorkArea->taskTab[$i] = $this;
	}

	function addPacket($p, $old) {
		if ($this->input === null) {
			$this->input = $p;
			$this->packet_pending = true;
			if ($this->priority > $old->priority) {
				return $this;
			}
		} else {
			$p->append_to($this->input);
		}
		return $old;
	}

	function runTasks() {
		if ($this->isWaitingWithPacket()) {
			$msg = $this->input;
			$this->input = $msg->link;
			if ($this->input === null) {
				$this->running();
			} else {
				$this->packetPending();
			}
		} else {
			$msg = null;
		}
		return $this->fn($msg, $this->handle);
	}

	function waitTask() {
		$this->task_waiting = true;
		return $this;
	}

	function hold() {
		global $taskWorkArea;

		$taskWorkArea->holdCount += 1;
		$this->task_holding = true;
		return $this->link;
	}

	function release($i) {
		$t = $this->findtcb($i);
		$t->task_holding = false;
		if ($t->priority > $this->priority) {
			return $t;
		} else {
			return $this;
		}
	}

	function qpkt($pkt) {
		global $taskWorkArea;
		$t = $this->findtcb($pkt->ident);
		$taskWorkArea->qpktCount += 1;
		$pkt->link = null;
		$pkt->ident = $this->ident;
		return $t->addPacket($pkt, $this);
	}

	function findtcb($id) {
		global $taskWorkArea;
		$t = $taskWorkArea->taskTab[$id];
		if ($t === null) {
			throw new Exception("Bad task id");
		}
		return $t;
	}
}

class DeviceTask extends Task {
	function fn($pkt, $r) {
		$d = $r;
		if (!($d instanceof DeviceTaskRec)) {
			throw new Exception("not a DeviceTaskRec");
		}
		if ($pkt == null) {
			$pkt = $d->pending;
			if ($pkt === null)
				return $this->waitTask();
			$d->pending = null;
			return $this->qpkt($pkt);
		}
		$d->pending = $pkt;
		if (TRACING) {
			trace($pkt->datum);
		}
		return $this->hold();
	}
}

class HandlerTask extends Task {
	function fn($pkt, $r) {
		$h = $r;
		if (!($h instanceof HandlerTaskRec)) {
			throw new Exception("not a HandlerTaskRec");
		}
		if ($pkt !== null) {
			if ($pkt->kind == K_WORK)
				$h->workInAdd($pkt);
			else
				$h->deviceInAdd($pkt);
		}
		$work = $h->work_in;
		if ($work === null)
			return $this->waitTask();
		$count = $work->datum;
		if ($count >= BUFSIZE) {
			$h->work_in = $work->link;
			return $this->qpkt($work);
		}

		$dev = $h->device_in;
		if ($dev === null)
			return $this->waitTask();

		$h->device_in = $dev->link;
		$dev->datum = $work->data[$count];
		$work->datum = $count + 1;
		return $this->qpkt($dev);
	}
}

class IdleTask extends Task {
	function fn($pkt, $r) {
		$i = $r;
		if (!($i instanceof IdleTaskRec)) {
			throw new Exception("not an IdleTaskRec");
		}
		$i->count -= 1;
		if ($i->count == 0)
			return $this->hold();
		else if (($i->control & 1) == 0) {
			$i->control = $i->control / 2;
			return $this->release(I_DEVA);
		}
		$i->control = ($i->control / 2) ^ 0xd008;
		return $this->release(I_DEVB);
	}
}

class WorkTask extends Task {
	function fn($pkt, $r) {
		$w = $r;
		if ($pkt === null)
			return $this->waitTask();

		if ($w->destination == I_HANDLERA)
			$dest = I_HANDLERB;
		else
			$dest = I_HANDLERA;

		$w->destination = $dest;
		$pkt->ident = $dest;
		$pkt->datum = 0;

		for ($i = 0; $i < BUFSIZE; $i++) {
			$w->count += 1;
			if ($w->count > 26)
				$w->count = 1;
			$pkt->data[$i] = ord("A") + $w->count - 1;
		}

		return $this->qpkt($pkt);
	}
}

define('TRACING', 0);

function schedule() {
	global $taskWorkArea;

	$t = $taskWorkArea->taskList;
	while ($t !== null) {
		$pkt = null;
		if (TRACING)
			printf("tcb = %d\n", $t->ident);
		if ($t->isTaskHoldingOrWaiting())
			$t = $t->link;
		else {
			if (TRACING)
				trace(chr(ord("0") + $t->ident));
			$t = $t->runTasks();
		}
	}
}

class Richards {

	function run($iterations) {
		global $taskWorkArea;

		for ($i = 0; $i < $iterations; $i++) {
			$taskWorkArea->holdCount = 0;
			$taskWorkArea->qpktCount = 0;
			$task_state = new TaskState();
			new IdleTask(I_IDLE, 1, 10000, $task_state->running(),
			new IdleTaskRec());

			$wkq = new Packet(null, 0, K_WORK);
			$wkq = new Packet($wkq, 0, K_WORK);
			$task_state = new TaskState();
			new WorkTask(I_WORK, 1000, $wkq, $task_state->waitingWithPacket(),
			new WorkTaskRec());

			$wkq = new Packet(null, I_DEVA, K_DEV);
			$wkq = new Packet($wkq, I_DEVA, K_DEV);
			$wkq = new Packet($wkq, I_DEVA, K_DEV);
			$task_state = new TaskState();
			new HandlerTask(I_HANDLERA, 2000, $wkq,
			$task_state->waitingWithPacket(),
			new HandlerTaskRec());

			$wkq = new Packet(null, I_DEVB, K_DEV);
			$wkq = new Packet($wkq, I_DEVB, K_DEV);
			$wkq = new Packet($wkq, I_DEVB, K_DEV);
			$task_state = new TaskState();
			new HandlerTask(I_HANDLERB, 3000, $wkq,
			$task_state->waitingWithPacket(),
			new HandlerTaskRec());

			$wkq = null;

			$task_state = new TaskState();
			new DeviceTask(I_DEVA, 4000, $wkq, $task_state->waiting(),
			new DeviceTaskRec());
			$task_state = new TaskState();
			new DeviceTask(I_DEVB, 5000, $wkq, $task_state->waiting(),
			new DeviceTaskRec());

			schedule();

			if (!($taskWorkArea->holdCount == 9297 && $taskWorkArea->qpktCount == 23246))
				return false;
		}
		return true;
	}
}

$taskWorkArea = new TaskWorkArea();

$number_of_runs = 100;
if ($argc > 1) {
	$number_of_runs = $argv[1] + 0;
}

$r = new Richards();
$t0 = microtime(true);
$res = $r->run($number_of_runs);
$t1 = microtime(true);

$total = $t1 - $t0;
printf("Richards (%s) took %.2fms, %.2fms per run\n", $number_of_runs, $total * 1000, $total * 1000 / $number_of_runs);

?>