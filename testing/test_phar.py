import py
import os
import tempfile
from testing.test_interpreter import BaseTestInterpreter, hippy_fail

from hippy.module.phar import utils


class TestPhar(BaseTestInterpreter):

    def test_phar_object(self, tmpdir):
        output = self.run('''
            ini_set('phar.readonly', false);
            $p = new Phar('%s/newphar.tar.phar', 0, 'newphar.tar.phar');
            echo get_class($p);
        ''' % tmpdir)

        assert self.space.str_w(output[0]) == 'Phar'

    def test_count(self):
        phar_file = os.path.join(os.path.dirname(__file__), 'phar_files/phar.phar')
        output = self.run('''
            $p = new Phar('%s');
            echo $p->count();
        ''' % phar_file)

        assert self.space.int_w(output[0]) == 2

    @hippy_fail(reason='Not implemented')
    def test_create_phar(self, tmpdir):
        output = self.run('''
        $p = new Phar('{0}/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p->startBuffering();
        $p['file1.txt'] = 'Information';
        $p->stopBuffering();
        $p2 = new Phar('{0}/newphar.tar.phar', 0);
        foreach (new RecursiveIteratorIterator($p2) as $file) {{
            echo $file->getFileName();
            echo file_get_contents($file->getPathName());
            }}
        unset($p);
        unset($p2);
        Phar::unlinkArchive('{0}/newphar.tar.phar');
        '''.format(tmpdir))
        assert len(output) == 2
        assert self.space.str_w(output[0]) == 'file1.txt'
        assert self.space.str_w(output[1]) == 'Information'

    @hippy_fail(reason='Not implemented')
    def test_add_empty_dir(self, tmpdir):
        tmpdir.mkdir('subdir')
        output = self.run('''
        $p = new Phar('{0}/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p->startBuffering();
        $p['file1.txt'] = 'Information';
        $p->stopBuffering();

        $p2 = new Phar('{0}/newphar.tar.phar', 0);
        $p2->addEmptyDir('{0}/subdir');
        echo $p2['{0}/subdir']->isDir();        // TODO: Catch exception on failure
        unset($p);
        unset($p2);
        Phar::unlinkArchive('{0}/newphar.tar.phar');
        '''.format(tmpdir))
        assert output[0] == self.space.w_True

    def test_add_file(self, tmpdir):
        tmpdir.join('foo.txt').write('Foo')
        output = self.run('''
        $p = new Phar('{0}/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p->addFile('{0}/foo.txt');
        echo $p['{0}/foo.txt']->getContent();
        unset($p);
        Phar::unlinkArchive('{0}/newphar.tar.phar');
        '''.format(tmpdir))
        assert self.space.str_w(output[0]) == 'Foo'

    def test_add_from_string(self, tmpdir):
        output = self.run('''
        $p = new Phar('{0}/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p->addFromString('test/path/foo.txt', 'Bar');
        echo $p['test/path/foo.txt']->getContent();
        unset($p);
        Phar::unlinkArchive('{0}/newphar.tar.phar');
       '''.format(tmpdir))
        assert self.space.str_w(output[0]) == 'Bar'

    def test_api_version(self):
        output = self.run('''
        echo Phar::apiVersion();
        ''')
        assert self.space.str_w(output[0]) == '1.1.1'       # TODO: Will this be true always?

    def test_get_version(self):
        phar_file = os.path.join(os.path.dirname(__file__), 'phar_files/phar.phar')

        output = self.run('''

            $p = new Phar('%s');
            echo $p->getVersion();

        ''' % phar_file)
        assert self.space.str_w(output[0]) == '1.1.0' # 1.1.1 will be for phar having at least one dir inside

    @hippy_fail(reason='Not implemented')
    def test_build_from_directory(self, tmpdir):
        tempdir = py.path.local(tempfile.mkdtemp())
        tmpdir.join('foo.txt').write('test file 1')
        tmpdir.join('bar.txt').write('test file 2')
        output = self.run('''
        $p = new Phar('{0}/newphar4.tar.phar', 0, 'newphar4.tar.phar');
        $p->buildFromDirectory('{0}');

        $p = new Phar('{0}/newphar4.tar.phar');
        foreach (new RecursiveIteratorIterator($p) as $file) {{
            echo $file->getFileName();
            echo file_get_contents($file->getPathName());
            }}
        '''.format(tmpdir))

        assert len(output) == 4
        assert self.space.newstr('foo.txt') in output
        assert self.space.newstr('test file 1') in output
        assert self.space.newstr('bar.txt') in output
        assert self.space.newstr('test file 2') in output

    def test_offset_exists(self):
        phar_file = os.path.join(
            os.path.dirname(__file__),
            'phar_files/onefilein.phar'
        )

        output = self.run('''
        $p = new Phar('%s');
        echo isset($p['foo.txt']);
        echo isset($p['bar.txt']);
        ''' % phar_file)
        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_False

    def test_offset_get(self):
        phar_file = os.path.join(
            os.path.dirname(__file__),
            'phar_files/onefilein.phar'
        )
        output = self.run('''
        $p = new Phar('%s');
        try {
            $res = $p['foo.txt'];
            echo get_class($res);
            echo $res->getContent();
            echo $p['bar.txt'];
        } catch (BadMethodCallException $e) {
            echo $e->getMessage();
        }
        ''' % phar_file)
        assert self.space.str_w(output[0]) == 'PharFileInfo'
        assert self.space.str_w(output[1]) == 'Foo'
        assert self.space.str_w(output[2]) == 'Entry bar.txt does not exist'

    def test_offset_unset(self, tmpdir):
        output = self.run('''
        $p = new Phar('{0}/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p['foo.txt'] = "File exists";
        try {{
            echo $p['foo.txt']->getContent();
            unset($p['foo.txt']);
            echo $p['foo.txt']->getContent();
        }} catch (BadMethodCallException $e) {{
            echo $e->getMessage();
        }}
        unset($p);
        Phar::unlinkArchive('{0}/newphar.tar.phar');
        '''.format(tmpdir))
        assert self.space.str_w(output[0]) == 'File exists'
        assert self.space.str_w(output[1]) == 'Entry foo.txt does not exist'

    def test_is_buffering(self, tmpdir):
        output = self.run('''
        $p1 = new Phar('{0}/newphar1.tar.phar', 0, 'newphar1.tar.phar');
        $p1['foo.txt'] = "Foo";
        $p2 = new Phar('{0}/newphar2.tar.phar', 0, 'newphar2.tar.phar');
        $p2['bar.txt'] = "Bar";
        $p1->startBuffering();
        echo $p1->isBuffering();
        echo $p2->isBuffering();
        $p1->stopBuffering();
        echo $p1->isBuffering();
        '''.format(tmpdir))
        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_False
        assert output[2] == self.space.w_False

    @hippy_fail(reason='Not implemented')
    def test_compress_files_gz(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar000.phar', 0, 'newphar000.phar');
        $p['myfile1.txt'] = 'Foo.';
        $p['myfile2.txt'] = 'Bar.';
        // XXX: why is this needed??
        $p = new Phar('%s/newphar000.phar', 0, 'newphar000.phar');
        foreach ($p as $file) {
            echo $file->isCompressed();
            echo $file->isCompressed(Phar::GZ);
            echo $file->isCompressed(Phar::BZ2);
        }
        $p->compressFiles(Phar::GZ);
        foreach ($p as $file) {
            echo $file->isCompressed();
            echo $file->isCompressed(Phar::GZ);
            echo $file->isCompressed(Phar::BZ2);
        }
        ''' % (tmpdir, tmpdir))
        assert len(output) == 12
        for i in range(6):
            assert output[i] == self.space.w_False
        i = 6
        while i < 12:
            assert output[i] == self.space.w_True
            assert output[i+1] == self.space.w_True
            assert output[i+2] == self.space.w_False
            i = i + 3

    @hippy_fail(reason='Not implemented')
    def test_compress_files_bz2(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar001.phar', 0, 'newphar001.phar');
        $p['myfile1.txt'] = 'Foo.';
        $p['myfile2.txt'] = 'Bar.';
        unset($p);  // XXX: why is this needed??
        $p = new Phar('%s/newphar001.phar', 0, 'newphar001.phar');
        foreach ($p as $file) {
            echo $file->isCompressed();
            echo $file->isCompressed(Phar::GZ);
            echo $file->isCompressed(Phar::BZ2);
        }
        $p->compressFiles(Phar::BZ2);
        foreach ($p as $file) {
            echo $file->isCompressed();
            echo $file->isCompressed(Phar::GZ);
            echo $file->isCompressed(Phar::BZ2);
        }
        ''' % (tmpdir, tmpdir))
        assert len(output) == 12
        for i in range(6):
            assert output[i] == self.space.w_False
        i = 6
        while i < 12:
            assert output[i] == self.space.w_True
            assert output[i+1] == self.space.w_False
            assert output[i+2] == self.space.w_True
            i = i + 3

    @hippy_fail(reason='Not implemented')
    def test_compress_gz(self, tmpdir):
        output = self.run('''
        $p = new Phar('{0}/newphar.phar', 0, 'newphar.phar');
        $p['myfile1.txt'] = 'Foo';
        $p['myfile2.txt'] = 'Bar';
        $p1 = $p->compress(Phar::GZ);
        echo get_class($p1);
        echo $p1->isCompressed();
        '''.format(tmpdir))
        assert self.space.str_w(output[0]) == 'Phar'
        assert self.space.int_w(output[1]) == 4096

    @hippy_fail(reason='Not implemented')
    def test_compress_bz2(self, tmpdir):
        output = self.run('''
        $p = new Phar('{0}/newphar.phar', 0, 'newphar.phar');
        $p['myfile1.txt'] = 'Foo';
        $p['myfile2.txt'] = 'Bar';
        $p1 = $p->compress(Phar::BZ2);
        echo get_class($p1);
        echo $p1->isCompressed();
        '''.format(tmpdir))
        assert self.space.str_w(output[0]) == 'Phar'
        assert self.space.int_w(output[1]) == 8192

    @hippy_fail(reason='Not implemented')
    def test_compress_none(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar.phar', 0, 'newphar.phar');
        $p['myfile1.txt'] = 'Foo';
        $p['myfile2.txt'] = 'Bar';
        try{
            $p1 = $p->compress(Phar::NONE);
        } catch (BadMethodCallException $e) {
            echo $e->getMessage();
        }
        ''' % tmpdir)
        assert self.space.str_w(output[0]) == (
            'Unable to add newly converted phar "%s/newphar.phar" to the list '
            'of phars, a phar with that name already exists' % tmpdir)

    def test_copy(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar.phar', 0, 'newphar.phar');
        $p['a'] = 'foo';
        echo $p->copy('a', 'b');
        echo $p['b']->getContent();
        ''' % tmpdir)
        assert output[0] == self.space.w_True
        assert self.space.str_w(output[1]) == 'foo'

    def test_metadata(self, tmpdir):    # XXX: Implemented hasMetadata()
        output = self.run('''
        $p = new Phar('%s/newphar.phar', 0, 'newphar.phar');
        $p['file.php'] = '<?php echo "hello";';
        echo $p->hasMetadata();
        $p->setMetadata(array('bootstrap' => 'file.php'));
        echo $p->hasMetadata();
        echo $p->getMetadata();
        echo $p->delMetadata();
        echo $p->hasMetadata();
        ''' % tmpdir)
        assert output[0] == self.space.w_False
        assert output[1] == self.space.w_True
        from hippy.objects.arrayobject import W_RDictArrayObject
        assert isinstance(output[2], W_RDictArrayObject)
        for key, w_value in output[2].dct_w.iteritems():
            assert key == 'bootstrap'
            assert self.space.str_w(w_value) == 'file.php'
        assert output[3] == self.space.w_True
        assert output[4] == self.space.w_False

    @hippy_fail(reason='Not implemented')
    def test_running(self, tmpdir):
        output = self.run('''
        echo Phar::running();
        $p = new Phar('{0}/newphar.phar', 0, 'newphar.phar');
        $p['foo.php'] = '<?php echo Phar::running(); echo Phar::running(false); ?>';
        include 'phar://{0}/newphar.phar/foo.php';
        echo Phar::running();
        '''.format(tmpdir))
        assert len(output) == 4
        assert self.space.str_w(output[0]) == ''
        assert self.space.str_w(output[1]) == 'phar://%s/newphar.phar' % tmpdir
        assert self.space.str_w(output[2]) == '%s/newphar.phar' % tmpdir
        assert self.space.str_w(output[3]) == ''

    @hippy_fail(reason='Not implemented')
    def test_intercept_file_funcs(self, tmpdir):
        output = self.run('''
        $p = new Phar('{0}/newphar.phar', 0, 'newphar.phar');
        $p['foo.txt'] = 'Test file.';
        $p['file.php'] = "<?php echo file_get_contents('foo.txt'); ?>";
        Phar::interceptFileFuncs();
        include 'phar://{0}/newphar.phar/file.php';
        '''.format(tmpdir))
        assert self.space.str_w(output[0]) == 'Test file.'

    @hippy_fail(reason='Not implemented')
    def test_modified(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar.phar', 0, 'newphar.phar');
        echo $p->getModified();
        $p['a'] = 'foo';
        $p->compressFiles(Phar::GZ);
        echo $p->getModified();
        ''' % tmpdir)
        assert output[0] == self.space.w_False
        assert output[1] == self.space.w_True

    def test_signature(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar.phar', 0, 'newphar.phar');
        $p['a'] = 'foo';
        echo $p->getSignature();
        ''' % tmpdir)
        from hippy.objects.arrayobject import W_RDictArrayObject
        assert isinstance(output[0], W_RDictArrayObject)
        for key, w_value in output[0].dct_w.iteritems():
            assert key in ['hash', 'hash_type']

    @hippy_fail(reason='Not implemented')
    def test_load_phar(self, tmpdir):
        output = self.run('''
        $p = new Phar('{0}/newphar.phar');
        $p['foo.txt'] = 'Foo';
        Phar::loadPhar('{0}/newphar.phar', 'test.phar');
        echo file_get_contents('phar://test.phar/foo.txt');
        '''.format(tmpdir))
        assert self.space.str_w(output[0]) == 'Foo'

    @hippy_fail(reason='Not implemented')
    def test_set_alias(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar.phar');
        $p['foo.txt'] = 'Foo';
        $p->setAlias('test.phar');
        echo file_get_contents('phar://test.phar/foo.txt');
        ''' % tmpdir)
        assert self.space.str_w(output[0]) == 'Foo'

    @hippy_fail(reason='Not implemented')
    def test_uncompressallfiles(self, tmpdir):
        orig = py.path.local(__file__).join('../phar_files/testfilesbz2.phar')
        orig.copy(tmpdir.join('testfilesbz2.phar'))

        output = self.run('''
        $p = new Phar('%s/testfilesbz2.phar');
        foreach ($p as $file) {
            echo $file->isCompressed();
            echo $file->isCompressed(Phar::GZ);
            echo $file->isCompressed(Phar::BZ2);
        }
        $p->decompressFiles();
        foreach ($p as $file) {
            echo $file->isCompressed();
            echo $file->isCompressed(Phar::GZ);
            echo $file->isCompressed(Phar::BZ2);
        }
        ''' % tmpdir)
        assert len(output) == 12
        i = 0
        while i < 6:
            assert output[i] == self.space.w_True
            assert output[i+1] == self.space.w_False
            assert output[i+2] == self.space.w_True
            i += 3
        while i < 12:
            assert output[i] == self.space.w_False
            i += 1

    @hippy_fail(reason='Not implemented')
    def test_decompress_bz2_phar(self, tmpdir):
        orig = py.path.local(__file__).join('../phar_files/testbz2.phar.bz2')
        orig.copy(tmpdir.join('testbz2.phar.bz2'))
        output = self.run('''
            $p = new Phar('%s/testbz2.phar.bz2');
            echo $p->isCompressed();

            $p1 = $p->decompress();
            echo get_class($p1);
            echo $p1->isCompressed();
        ''' % tmpdir)
        assert self.space.int_w(output[0]) == 8192
        assert self.space.str_w(output[1]) == 'Phar'
        assert output[2] == self.space.w_False

    @hippy_fail(reason='Not implemented')
    def test_decompress_gz_phar(self, tmpdir):
        orig = py.path.local(__file__).join('../phar_files/testgz.phar.gz')
        orig.copy(tmpdir.join('testgz.phar.gz'))
        output = self.run('''
            $p = new Phar('%s/testgz.phar.gz');
            echo $p->isCompressed();

            $p1 = $p->decompress();
            echo get_class($p1);
            echo $p1->isCompressed();
        ''' % tmpdir)
        assert self.space.int_w(output[0]) == 4096
        assert self.space.str_w(output[1]) == 'Phar'
        assert output[2] == self.space.w_False

    @hippy_fail(reason='Not implemented')
    def test_stub(self, tmpdir):
        output = self.run('''
            $p = new Phar('%s/brandnewphar.phar', 0, 'brandnewphar.phar');
            $p['a.php'] = '<?php echo "Hello";';
            $p->setStub('<?php var_dump("First"); Phar::mapPhar("brandnewphar.phar"); __HALT_COMPILER(); ?>');
            include 'phar://brandnewphar.phar/a.php';
            echo $p->getStub();
            $p['b.php'] = '<?php echo "World";';
            $p->setStub('<?php var_dump("Second"); Phar::mapPhar("brandnewphar.phar"); __HALT_COMPILER(); ?>');
            include 'phar://brandnewphar.phar/b.php';
            echo $p->getStub();
            unset($p);
            Phar::unlinkArchive('%s/brandnewphar.phar');
        ''' % (tmpdir, tmpdir))
        assert len(output) == 4
        assert self.space.str_w(output[0]) == 'Hello'
        assert self.space.str_w(output[1]) == '<?php var_dump("First"); Phar::mapPhar("brandnewphar.phar"); __HALT_COMPILER(); ?>\r\n'
        assert self.space.str_w(output[2]) == 'World'
        assert self.space.str_w(output[3]) == '<?php var_dump("Second"); Phar::mapPhar("brandnewphar.phar"); __HALT_COMPILER(); ?>\r\n'

    @hippy_fail(reason='Not implemented')
    def test_is_file_format(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar.phar', 0, 'newphar.phar');
        $p['myfile1.txt'] = 'Foo';
        echo $p->isFileFormat(Phar::PHAR);
        echo $p->isFileFormat(Phar::TAR);
        echo $p->isFileFormat(Phar::ZIP);
        ''' % tmpdir)
        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_False
        assert output[2] == self.space.w_False

    @hippy_fail(reason='Not implemented')
    def test_is_valid_phar_filename(self):
        output = self.run('''
        echo Phar::isValidPharFilename('anyNameWillDo.phar');
        echo Phar::isValidPharFilename('anyNameWill.Do');
        echo Phar::isValidPharFilename('anyNameWillDo');
        echo Phar::isValidPharFilename('anyNameWillDo', false);
        echo Phar::isValidPharFilename('anyNameWill.Do', false);
        ''')
        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_False
        assert output[2] == self.space.w_False
        assert output[3] == self.space.w_False
        assert output[4] == self.space.w_True

    def test_is_writable(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar.phar', 0, 'newphar.phar');
        $p['myfile1.txt'] = 'Foo';
        echo $p->isWritable();
        ''' % tmpdir)
        assert output[0] == self.space.w_True

    def test_delete(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar.phar', 0, 'newphar.phar');
        $p['foo.txt'] = 'Foo';
        $p['bar.txt'] = 'Bar';
        echo $p->count();
        echo $p->delete('foo.txt');
        echo $p->count();
        ''' % tmpdir)
        assert self.space.int_w(output[0]) == 2
        assert output[1] == self.space.w_True
        assert self.space.int_w(output[2]) == 1


class TestPharFileInfo(BaseTestInterpreter):

    @hippy_fail(reason='Not implemented')
    def test_chmod(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar.phar', 0, 'newphar.phar');
        $p['foo.sh'] = '#!/usr/local/lib/php <?php echo "Testing!"; ?>';
        echo $p['foo.sh']->isExecutable();
        $p['foo.sh']->chmod(0555);
        echo $p['foo.sh']->isExecutable();
        ''' % tmpdir)
        assert output[0] == self.space.w_False
        assert output[1] == self.space.w_True

    @hippy_fail(reason='Not implemented')
    def test_compress(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar.phar', 0, 'newphar.phar');
        $p['myfile.txt'] = 'hi';
        $file = $p['myfile.txt'];
        echo $file->isCompressed(Phar::BZ2);
        echo $p['myfile.txt']->compress(Phar::BZ2);
        echo $file->isCompressed(Phar::BZ2);
        ''' % tmpdir)
        assert output[0] == self.space.w_False
        assert output[1] == self.space.w_True
        assert output[2] == self.space.w_True

    @hippy_fail(reason='Not implemented')
    def test_decompress(self, tmpdir):
        output = self.run('''
        $p = new Phar('%s/newphar.phar', 0, 'newphar.phar');
        $p['myfile.txt'] = 'hi';
        $file = $p['myfile.txt'];
        $file->compress(Phar::BZ2);
        echo $file->isCompressed(Phar::BZ2);
        echo $file->decompress();
        echo $file->isCompressed();
        ''' % tmpdir)
        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_True
        assert output[2] == self.space.w_False

    def test_is_compressed(self):
        phar_file = os.path.join(
            os.path.dirname(__file__),
            'phar_files/onefilein.phar'
        )
        output = self.run('''
            $p = new Phar('%s');
            $file_info = $p['foo.txt'];
            echo $file_info->isCompressed();
        ''' % phar_file)
        assert output[0] == self.space.w_False

    def test_metadata(self, tmpdir):
        output = self.run('''
        $p = new Phar('{0}/newphar.phar', 0, 'newphar.phar');
        $p['foo'] = 'Foo.';
        $p['foo']->setMetadata('Bar');
        echo $p['foo']->hasMetadata();
        echo $p['foo']->getMetadata();
        echo $p['foo']->delMetadata();
        echo $p['foo']->hasMetadata();
        echo $p['foo']->getMetadata();
        echo $p['foo']->delMetadata();
        '''.format(tmpdir))
        assert output[0] == self.space.w_True
        assert self.space.str_w(output[1]) == 'Bar'
        assert output[2] == self.space.w_True
        assert output[3] == self.space.w_False
        assert output[4] == self.space.w_Null
        assert output[5] == self.space.w_True      # XXX: Always returns true. Sadness.

    def test_get_phar_flags(self):
        phar_file = os.path.join(
            os.path.dirname(__file__),
            'phar_files/onefilein.phar'
        )
        output = self.run('''
        $p = new Phar('%s');
        echo $p['foo.txt']->getPharFlags();
        ''' % phar_file)
        assert self.space.int_w(output[0]) == 0

    def test_get_compressed_size(self):
        phar_file = os.path.join(
            os.path.dirname(__file__),
            'phar_files/onefilein.phar'
        )
        output = self.run('''
        $p = new Phar('%s');
        echo $p['foo.txt']->getCompressedSize();
        ''' % phar_file)
        assert self.space.int_w(output[0]) == 3

    def test_is_crc_checked(self):
        phar_file = os.path.join(
            os.path.dirname(__file__),
            'phar_files/onefilein.phar'
        )
        output = self.run('''
        $p = new Phar('%s');
        echo $p['foo.txt']->isCRCChecked();
        ''' % phar_file)
        assert output[0] == self.space.w_True


class TestPharUtils(BaseTestInterpreter):

    def test_generate_stub(self):
        stub = utils.generate_stub('index.php', 'index.php')
        assert len(stub) == 6683

    def test_fetch_phar_data(self):
        phar_file = os.path.join(os.path.dirname(__file__), 'phar_files/phar.phar')
        phar_content = open(phar_file, 'r').read()

        stub, phar_data = utils.fetch_phar_data(phar_content)
        phar = utils.read_phar(self.space, phar_data)
        new_phar_data = utils.write_phar(self.space, phar, stub)
        assert new_phar_data == phar_data
        assert phar.files_count == 2
        assert len(phar.files) == 2

        assert 'test.php' in phar.files.keys()
        assert 'test2.php' in phar.files.keys()

        assert phar.files['test.php'].name_length == 8
        assert phar.files['test.php'].size_uncompressed == 18
        assert phar.files['test.php'].timestamp == 1401356104
        assert phar.files['test.php'].content == '<?php echo "seba";'
        assert len(phar.files['test.php'].content) == 18


        assert phar.files['test2.php'].name_length == 9
        assert phar.files['test2.php'].size_uncompressed == 18
        assert phar.files['test2.php'].timestamp == 1401356104
        assert phar.files['test2.php'].content == '<?php echo "ALA";\n'
        assert len(phar.files['test2.php'].content) == 18
