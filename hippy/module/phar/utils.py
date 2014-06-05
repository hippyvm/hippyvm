from collections import OrderedDict

from hippy.module import phpstruct
from hippy.lexer import Lexer

def get_stub(web, index):
    stub_len = len(template) + len(web) + len(index) + 5;
    return template % (web, index, stub_len)

template = """<?php

$web = '%s';

if (in_array('phar', stream_get_wrappers()) && class_exists('Phar', 0)) {
Phar::interceptFileFuncs();
set_include_path('phar://' . __FILE__ . PATH_SEPARATOR . get_include_path());
Phar::webPhar(null, $web);
include 'phar://' . __FILE__ . '/' . Extract_Phar::START;
return;
}

if (@(isset($_SERVER['REQUEST_URI']) && isset($_SERVER['REQUEST_METHOD']) && ($_SERVER['REQUEST_METHOD'] == 'GET' || $_SERVER['REQUEST_METHOD'] == 'POST'))) {
Extract_Phar::go(true);
$mimes = array(
'phps' => 2,
'c' => 'text/plain',
'cc' => 'text/plain',
'cpp' => 'text/plain',
'c++' => 'text/plain',
'dtd' => 'text/plain',
'h' => 'text/plain',
'log' => 'text/plain',
'rng' => 'text/plain',
'txt' => 'text/plain',
'xsd' => 'text/plain',
'php' => 1,
'inc' => 1,
'avi' => 'video/avi',
'bmp' => 'image/bmp',
'css' => 'text/css',
'gif' => 'image/gif',
'htm' => 'text/html',
'html' => 'text/html',
'htmls' => 'text/html',
'ico' => 'image/x-ico',
'jpe' => 'image/jpeg',
'jpg' => 'image/jpeg',
'jpeg' => 'image/jpeg',
'js' => 'application/x-javascript',
'midi' => 'audio/midi',
'mid' => 'audio/midi',
'mod' => 'audio/mod',
'mov' => 'movie/quicktime',
'mp3' => 'audio/mp3',
'mpg' => 'video/mpeg',
'mpeg' => 'video/mpeg',
'pdf' => 'application/pdf',
'png' => 'image/png',
'swf' => 'application/shockwave-flash',
'tif' => 'image/tiff',
'tiff' => 'image/tiff',
'wav' => 'audio/wav',
'xbm' => 'image/xbm',
'xml' => 'text/xml',
);

header("Cache-Control: no-cache, must-revalidate");
header("Pragma: no-cache");

$basename = basename(__FILE__);
if (!strpos($_SERVER['REQUEST_URI'], $basename)) {
chdir(Extract_Phar::$temp);
include $web;
return;
}
$pt = substr($_SERVER['REQUEST_URI'], strpos($_SERVER['REQUEST_URI'], $basename) + strlen($basename));
if (!$pt || $pt == '/') {
$pt = $web;
header('HTTP/1.1 301 Moved Permanently');
header('Location: ' . $_SERVER['REQUEST_URI'] . '/' . $pt);
exit;
}
$a = realpath(Extract_Phar::$temp . DIRECTORY_SEPARATOR . $pt);
if (!$a || strlen(dirname($a)) < strlen(Extract_Phar::$temp)) {
header('HTTP/1.0 404 Not Found');
echo "<html>\n <head>\n  <title>File Not Found<title>\n </head>\n <body>\n  <h1>404 - File ", $pt, " Not Found</h1>\n </body>\n</html>";
exit;
}
$b = pathinfo($a);
if (!isset($b['extension'])) {
header('Content-Type: text/plain');
header('Content-Length: ' . filesize($a));
readfile($a);
exit;
}
if (isset($mimes[$b['extension']])) {
if ($mimes[$b['extension']] === 1) {
include $a;
exit;
}
if ($mimes[$b['extension']] === 2) {
highlight_file($a);
exit;
}
header('Content-Type: ' .$mimes[$b['extension']]);
header('Content-Length: ' . filesize($a));
readfile($a);
exit;
}
}

class Extract_Phar
{
static $temp;
static $origdir;
const GZ = 0x1000;
const BZ2 = 0x2000;
const MASK = 0x3000;
const START = '%s';
const LEN = %s;

static function go($return = false)
{
$fp = fopen(__FILE__, 'rb');
fseek($fp, self::LEN);
$L = unpack('V', $a = (binary)fread($fp, 4));
$m = (binary)'';

do {
$read = 8192;
if ($L[1] - strlen($m) < 8192) {
$read = $L[1] - strlen($m);
}
$last = (binary)fread($fp, $read);
$m .= $last;
} while (strlen($last) && strlen($m) < $L[1]);

if (strlen($m) < $L[1]) {
die('ERROR: manifest length read was "' .
strlen($m) .'" should be "' .
$L[1] . '"');
}

$info = self::_unpack($m);
$f = $info['c'];

if ($f & self::GZ) {
if (!function_exists('gzinflate')) {
die('Error: zlib extension is not enabled -' .
' gzinflate() function needed for zlib-compressed .phars');
}
}

if ($f & self::BZ2) {
if (!function_exists('bzdecompress')) {
die('Error: bzip2 extension is not enabled -' .
' bzdecompress() function needed for bz2-compressed .phars');
}
}

$temp = self::tmpdir();

if (!$temp || !is_writable($temp)) {
$sessionpath = session_save_path();
if (strpos ($sessionpath, ";") !== false)
$sessionpath = substr ($sessionpath, strpos ($sessionpath, ";")+1);
if (!file_exists($sessionpath) || !is_dir($sessionpath)) {
die('Could not locate temporary directory to extract phar');
}
$temp = $sessionpath;
}

$temp .= '/pharextract/'.basename(__FILE__, '.phar');
self::$temp = $temp;
self::$origdir = getcwd();
@mkdir($temp, 0777, true);
$temp = realpath($temp);

if (!file_exists($temp . DIRECTORY_SEPARATOR . md5_file(__FILE__))) {
self::_removeTmpFiles($temp, getcwd());
@mkdir($temp, 0777, true);
@file_put_contents($temp . '/' . md5_file(__FILE__), '');

foreach ($info['m'] as $path => $file) {
$a = !file_exists(dirname($temp . '/' . $path));
@mkdir(dirname($temp . '/' . $path), 0777, true);
clearstatcache();

if ($path[strlen($path) - 1] == '/') {
@mkdir($temp . '/' . $path, 0777);
} else {
file_put_contents($temp . '/' . $path, self::extractFile($path, $file, $fp));
@chmod($temp . '/' . $path, 0666);
}
}
}

chdir($temp);

if (!$return) {
include self::START;
}
}

static function tmpdir()
{
if (strpos(PHP_OS, 'WIN') !== false) {
if ($var = getenv('TMP') ? getenv('TMP') : getenv('TEMP')) {
return $var;
}
if (is_dir('/temp') || mkdir('/temp')) {
return realpath('/temp');
}
return false;
}
if ($var = getenv('TMPDIR')) {
return $var;
}
return realpath('/tmp');
}

static function _unpack($m)
{
$info = unpack('V', substr($m, 0, 4));
 $l = unpack('V', substr($m, 10, 4));
$m = substr($m, 14 + $l[1]);
$s = unpack('V', substr($m, 0, 4));
$o = 0;
$start = 4 + $s[1];
$ret['c'] = 0;

for ($i = 0; $i < $info[1]; $i++) {
 $len = unpack('V', substr($m, $start, 4));
$start += 4;
 $savepath = substr($m, $start, $len[1]);
$start += $len[1];
   $ret['m'][$savepath] = array_values(unpack('Va/Vb/Vc/Vd/Ve/Vf', substr($m, $start, 24)));
$ret['m'][$savepath][3] = sprintf('%%u', $ret['m'][$savepath][3]
& 0xffffffff);
$ret['m'][$savepath][7] = $o;
$o += $ret['m'][$savepath][2];
$start += 24 + $ret['m'][$savepath][5];
$ret['c'] |= $ret['m'][$savepath][4] & self::MASK;
}
return $ret;
}

static function extractFile($path, $entry, $fp)
{
$data = '';
$c = $entry[2];

while ($c) {
if ($c < 8192) {
$data .= @fread($fp, $c);
$c = 0;
} else {
$c -= 8192;
$data .= @fread($fp, 8192);
}
}

if ($entry[4] & self::GZ) {
$data = gzinflate($data);
} elseif ($entry[4] & self::BZ2) {
$data = bzdecompress($data);
}

if (strlen($data) != $entry[0]) {
die("Invalid internal .phar file (size error " . strlen($data) . " != " .
$stat[7] . ")");
}

if ($entry[3] != sprintf("%%u", crc32((binary)$data) & 0xffffffff)) {
die("Invalid internal .phar file (checksum error)");
}

return $data;
}

static function _removeTmpFiles($temp, $origdir)
{
chdir($temp);

foreach (glob('*') as $f) {
if (file_exists($f)) {
is_dir($f) ? @rmdir($f) : @unlink($f);
if (file_exists($f) && is_dir($f)) {
self::_removeTmpFiles($f, getcwd());
}
}
}

@rmdir($temp);
clearstatcache();
chdir($origdir);
}
}

Extract_Phar::go();
__HALT_COMPILER(); ?>"""


def generate_stub(web, index):
    stub_len = len(template) + len(web) + len(index) + 5;
    return template % (web, index, stub_len)


def fetch_phar_data(content):

    lexer = Lexer()
    lexer.input(content, 0, 0)

    for token in lexer.token():
        if token.name == "T_HALT_COMPILER":
            ending_tag = content[token.source_pos.idx:].find("?>")
            if ending_tag != 1:
                return content[token.source_pos.idx + ending_tag + 2:]

    return ''


def write_phar(space, phar):
    # sig = { 'sha1': [('V', ), ()]}
    phar_data = phar.phar
    from hippy.module.hash.funcs import _get_hash_algo
    signature_type = {
        'md5': '\x01\x00\x00\x00',
        'sha1': '\x02\x00\x00\x00',
        'sha256': '\x04\x00\x00\x00',
        'sha512': '\x08\x00\x00\x00'
    }
    to_pack = [
        ('V', phar_data['length']),
        ('V', phar_data['files_count']),
        ('v', phar_data['api_version']),
        ('V', phar_data['flags']),
        ('V', phar_data['alias_length']),
        ('V', phar_data['global_metadata']),
    ]
    for fname, fdata in phar_data["files"].items():
        to_pack.append(('V', len(fname)))
        to_pack.append(('a*', fname))

        to_pack.append(('V', fdata['size_uncompressed']))
        to_pack.append(('V', fdata['timestamp']))
        to_pack.append(('V', fdata['size_compressed']))
        to_pack.append(('V', fdata['size_crc_uncompressed']))
        to_pack.append(('V', fdata['flags']))
        to_pack.append(('V', fdata['metadata']))

    algo = phar_data['signature_name']
    h = _get_hash_algo(algo)

    for _, fdata in phar_data["files"].items():
        to_pack.append(('a*', fdata['content']))

    format = ""
    args = []
    for fmt, val in to_pack:
        format += fmt
        args.append(space.wrap(val))
    new_phar = phpstruct.Pack(space, format, args).build()

    h.update(new_phar)
    signature = phpstruct.Pack(space, 'h', [space.wrap(h.hexdigest())]).build()

    new_phar += signature
    new_phar += signature_type[algo] + 'GBMB'
    return new_phar


def read_phar(data):
    data = data.lstrip()

    cursor = 0
    shift = 4+4+2+4+4

    manifest_data = phpstruct.Unpack("V/V/v/V/V", data[cursor:shift]).build()

    manifest = {
        "length": manifest_data[0][1],
        "files_count": manifest_data[1][1],
        "api_version": manifest_data[2][1],
        "flags": manifest_data[3][1],
        "alias_length": manifest_data[4][1]
    }

    if manifest["alias_length"]:
        cursor = shift
        shift = cursor+manifest["alias_length"]
        manifest["alias"] = data[cursor:shift]

    cursor = shift
    shift = cursor+4
    manifest_metadata = phpstruct.Unpack("V", data[cursor:shift]).build()[0][1]
    # XXX: Still not implemented, hack for Phar::hasMetadata()
    manifest["global_metadata"] = manifest_metadata

    if manifest_metadata:
        raise NotImplementedError()

    files = OrderedDict()
    for _ in range(int(manifest["files_count"])):
        cursor = shift
        shift = cursor+4
        file_name_length = phpstruct.Unpack("V", data[cursor:shift]).build()[0][1]

        cursor = shift
        shift = cursor+file_name_length
        file_name = phpstruct.Unpack("a*", data[cursor:shift]).build()[0][1]

        cursor = shift
        shift = cursor+4+4+4+4+4+4
        file_data = phpstruct.Unpack("V/V/V/V/V/V", data[cursor:shift]).build()

        cursor = shift

        file_size_uncompressed = file_data[0][1]
        file_timestamp = file_data[1][1]
        file_size_compressed = file_data[2][1]
        file_size_crc_uncompressed = file_data[3][1]
        file_flags = file_data[4][1]
        file_metadata = file_data[5][1]

        if file_metadata:
            raise NotImplementedError()

        files[file_name] = {
            "name_length": file_name_length,
            "size_uncompressed": file_size_uncompressed,
            "size_compressed": file_size_compressed,
            "timestamp": file_timestamp,
            "size_crc_uncompressed": file_size_crc_uncompressed,
            "flags": file_flags,
            "metadata": file_metadata
        }

    manifest['files'] = files

    # right now only plain phar files are supported
    for file_name, file_data in files.items():
        shift = cursor+file_data['size_uncompressed']
        files[file_name]['content'] = data[cursor:shift]
        cursor = shift

    gbmb = data.find("GBMB")
    if gbmb == -1:
        # raise something, but for now
        raise NotImplementedError

    signature_type = data[gbmb-4:gbmb]

    if signature_type == '\x01\x00\x00\x00':
        signature_length = 16
        signature_name = 'md5'

    elif signature_type == '\x02\x00\x00\x00':
        signature_length = 20
        signature_name = 'sha1'

    elif signature_type == '\x04\x00\x00\x00':
        signature_length = 32
        signature_name = 'sha256'

    elif signature_type == '\x08\x00\x00\x00':
        signature_length = 64
        signature_name = 'sha512'

    else:
        # raise something, but for now
        raise NotImplementedError

    manifest['signature'] = data[gbmb-signature_length-4:gbmb-4]
    manifest['signature_name'] = signature_name

    return manifest
