import py
import tempfile
from testing.test_interpreter import BaseTestInterpreter


class TestPhar(BaseTestInterpreter):

    def test_create_phar(self):
        output = self.run('''
        if (Phar::canWrite()) {
        $p = new Phar('/tmp/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p->startBuffering();
        $p['file1.txt'] = 'Information';
        $p->stopBuffering();
        }

        $p2 = new Phar('newphar0.tar.phar', 0);
        foreach (new RecursiveIteratorIterator($p2) as $file) {
            echo $file->getFileName();
            echo file_get_contents($file->getPathName());
            }
        unset($p);
        unset($p2);
        Phar::unlinkArchive('/tmp/newphar.tar.phar');
        ''')
        assert len(output) == 2
        assert self.space.str_w(output[0]) == 'file1.txt'
        assert self.space.str_w(output[1]) == 'Information'

    def test_add_empty_dir(self):
        tempdir = tempfile.mkdtemp()
        output = self.run('''
        if (Phar::canWrite()) {
        $p = new Phar('/tmp/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p->startBuffering();
        $p['file1.txt'] = 'Information';
        $p->stopBuffering();
        }

        $p2 = new Phar('newphar.tar.phar', 0);
        $p2->addEmptyDir('%s');
        echo $p2['%s']->isDir();        // TODO: Catch exception on failure
        unset($p);
        unset($p2);
        Phar::unlinkArchive('/tmp/newphar.tar.phar');
        ''' % (tempdir, tempdir))
        assert output[0] == self.space.w_True

    def test_add_file(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('Foo')
        output = self.run('''
        $p = new Phar('/tmp/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p->addFile('%s');
        echo $p['%s']->getContent();
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.tar.phar');
        ''' % (f, f))
        assert self.space.str_w(output[0]) == 'Foo'

    def test_add_from_string(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p->addFromString('test/path/foo.txt', 'Bar');
        echo $p['test/path/foo.txt']->getContent();
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.tar.phar');
       ''')
        assert self.space.str_w(output[0]) == 'Bar'

    def test_api_version(self):
        output = self.run('''
        echo Phar::apiVersion();
        ''')
        assert self.space.str_w(output[0]) == '1.1.1'       # TODO: Will this be true always?

    def test_get_version(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p['foo.txt'] = 'Foo.';
        echo $p->getVersion();
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.tar.phar');
        ''')
        assert self.space.str_w(output[0]) == '1.1.1'       # TODO: Will this be true always?

    def test_build_from_directory(self):            # XXX: Doesn't work on first run
        tempdir = py.path.local(tempfile.mkdtemp())
        f = tempdir.join('foo.txt')
        f.write('test file 1')
        f = tempdir.join('bar.txt')
        f.write('test file 2')
        output = self.run('''
        $p = new Phar('/tmp/newphar4.tar.phar', 0, 'newphar4.tar.phar');
        $p->buildFromDirectory(dirname('%s'));
        foreach (new RecursiveIteratorIterator($p) as $file) {
            echo $file->getFileName();
            echo file_get_contents($file->getPathName());
            }
//        unset($p);
//        Phar::unlinkArchive('/tmp/newphar.tar.phar');
        ''' % f)

        assert len(output) == 4
        assert self.space.newstr('foo.txt') in output
        assert self.space.newstr('test file 1') in output
        assert self.space.newstr('bar.txt') in output
        assert self.space.newstr('test file 2') in output

    def test_offset_exists(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p['foo.txt'] = 'Foo.';
        echo isset($p['foo.txt']);
        echo isset($p['bar.txt']);
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.tar.phar');
        ''')
        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_False

    def test_offset_get(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p['foo.txt'] = "File exists";
        try {
            $res = $p['foo.txt'];
            echo get_class($res);
            echo $res->getContent();
            echo $p['bar.txt'];
        } catch (BadMethodCallException $e) {
            echo $e->getMessage();
        }
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.tar.phar');
        ''')
        assert self.space.str_w(output[0]) == 'PharFileInfo'
        assert self.space.str_w(output[1]) == 'File exists'
        assert self.space.str_w(output[2]) == 'Entry bar.txt does not exist'

    def test_offset_unset(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.tar.phar', 0, 'newphar.tar.phar');
        $p['foo.txt'] = "File exists";
        try {
            echo $p['foo.txt']->getContent();
            unset($p['foo.txt']);
            echo $p['foo.txt']->getContent();
        } catch (BadMethodCallException $e) {
            echo $e->getMessage();
        }
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.tar.phar');
        ''')
        assert self.space.str_w(output[0]) == 'File exists'
        assert self.space.str_w(output[1]) == 'Entry foo.txt does not exist'

    def test_is_buffering(self):
        output = self.run('''
        $p1 = new Phar('/tmp/newphar1.tar.phar', 0, 'newphar1.tar.phar');
        $p1['foo.txt'] = "Foo";
        $p2 = new Phar('/tmp/newphar2.tar.phar', 0, 'newphar2.tar.phar');
        $p2['bar.txt'] = "Bar";
        $p1->startBuffering();
        echo $p1->isBuffering();
        echo $p2->isBuffering();
        $p1->stopBuffering();
        echo $p1->isBuffering();
        unset($p1);
        unset($p2);
        Phar::unlinkArchive('/tmp/newphar1.tar.phar');
        Phar::unlinkArchive('/tmp/newphar2.tar.phar');
        ''')
        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_False
        assert output[2] == self.space.w_False

    def test_compress_files_gz(self):       # XXX: Doesn't pass on first runs
        output = self.run('''
        $p = new Phar('/tmp/newphar000.phar', 0, 'newphar000.phar');
        $p['myfile1.txt'] = 'Foo.';
        $p['myfile2.txt'] = 'Bar.';
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
//        unset($p);
//        Phar::unlinkArchive('/tmp/newphar000.phar');
        ''')
        assert len(output) == 12
        for i in range(6):
            assert output[i] == self.space.w_False
        i = 6
        while i < 12:
            assert output[i] == self.space.w_True
            assert output[i+1] == self.space.w_True
            assert output[i+2] == self.space.w_False
            i = i + 3

    def test_compress_files_bz2(self):      # XXX: Doesn't pass on first runs

        output = self.run('''
        $p = new Phar('/tmp/newphar001.phar', 0, 'newphar001.phar');
        $p['myfile1.txt'] = 'Foo.';
        $p['myfile2.txt'] = 'Bar.';
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
//        unset($p);
//        Phar::unlinkArchive('/tmp/newphar001.phar');
        ''')
        assert len(output) == 12
        for i in range(6):
            assert output[i] == self.space.w_False
        i = 6
        while i < 12:
            assert output[i] == self.space.w_True
            assert output[i+1] == self.space.w_False
            assert output[i+2] == self.space.w_True
            i = i + 3

    def test_compress_gz(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar', 0, 'newphar.phar');
        $p['myfile1.txt'] = 'Foo';
        $p['myfile2.txt'] = 'Bar';
        $p1 = $p->compress(Phar::GZ);
        echo get_class($p1);
        echo $p1->isCompressed();
        unset($p);
        unset($p1);
        Phar::unlinkArchive('/tmp/newphar.phar');
        Phar::unlinkArchive('/tmp/newphar.phar.gz');
        ''')
        assert self.space.str_w(output[0]) == 'Phar'
        assert self.space.int_w(output[1]) == 4096

    def test_compress_bz2(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar', 0, 'newphar.phar');
        $p['myfile1.txt'] = 'Foo';
        $p['myfile2.txt'] = 'Bar';
        $p1 = $p->compress(Phar::BZ2);
        echo get_class($p1);
        echo $p1->isCompressed();
        unset($p);
        unset($p1);
        Phar::unlinkArchive('/tmp/newphar.phar');
        Phar::unlinkArchive('/tmp/newphar.phar.bz2');
        ''')
        assert self.space.str_w(output[0]) == 'Phar'
        assert self.space.int_w(output[1]) == 8192

    def test_compress_none(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar', 0, 'newphar.phar');
        $p['myfile1.txt'] = 'Foo';
        $p['myfile2.txt'] = 'Bar';
        try{
            $p1 = $p->compress(Phar::NONE);
        } catch (BadMethodCallException $e) {
            echo $e->getMessage();
        }
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.phar');
        ''')
        assert self.space.str_w(output[0]) == 'Unable to add newly converted phar "/tmp/newphar.phar" to the list of phars, a phar with that name already exists'

    def test_copy(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar', 0, 'newphar.phar');
        $p['a'] = 'foo';
        echo $p->copy('a', 'b');
        echo $p['b']->getContent();
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.phar');
        ''')
        assert output[0] == self.space.w_True
        assert self.space.str_w(output[1]) == 'foo'

    def test_count(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar', 0, 'newphar.phar');
        $p['a'] = 'foo';
        echo $p->count();
        $p['b'] = 'bar';
        echo $p->count();
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.phar');
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 2

    def test_metadata(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar', 0, 'newphar.phar');
        $p['file.php'] = '<?php echo "hello";';
        echo $p->hasMetadata();
        $p->setMetadata(array('bootstrap' => 'file.php'));
        echo $p->hasMetadata();
        echo $p->getMetadata();
        echo $p->delMetadata();
        echo $p->hasMetadata();
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.phar');
        ''')
        assert output[0] == self.space.w_False
        assert output[1] == self.space.w_True
        from hippy.objects.arrayobject import W_RDictArrayObject
        assert isinstance(output[2], W_RDictArrayObject)
        for key, w_value in output[2].dct_w.iteritems():
            assert key == 'bootstrap'
            assert self.space.str_w(w_value) == 'file.php'
        assert output[3] == self.space.w_True
        assert output[4] == self.space.w_False

    def test_running(self):
        output = self.run('''
        echo Phar::running();
        $p = new Phar('/tmp/newphar.phar', 0, 'newphar.phar');
        $p['foo.php'] = '<?php echo Phar::running(); echo Phar::running(false); ?>';
        include 'phar:///tmp/newphar.phar/foo.php';
        echo Phar::running();
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.phar');
        ''')
        assert len(output) == 4
        assert self.space.str_w(output[0]) == ''
        assert self.space.str_w(output[1]) == 'phar:///tmp/newphar.phar'
        assert self.space.str_w(output[2]) == '/tmp/newphar.phar'
        assert self.space.str_w(output[3]) == ''

    def test_intercept_file_funcs(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar', 0, 'newphar.phar');
        $p['foo.txt'] = 'Test file.';
        $p['file.php'] = "<?php echo file_get_contents('foo.txt'); ?>";
        Phar::interceptFileFuncs();
        include 'phar:///tmp/newphar.phar/file.php';
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.phar');
        ''')
        assert self.space.str_w(output[0]) == 'Test file.'

    def test_modified(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar', 0, 'newphar.phar');
        echo $p->getModified();
        $p['a'] = 'foo';
        $p->compressFiles(Phar::GZ);
        echo $p->getModified();
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.phar');
        ''')
        assert output[0] == self.space.w_False
        assert output[1] == self.space.w_True

    def test_signature(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar', 0, 'newphar.phar');
        $p['a'] = 'foo';
        echo $p->getSignature();
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.phar');
        ''')
        from hippy.objects.arrayobject import W_RDictArrayObject
        assert isinstance(output[0], W_RDictArrayObject)
        for key, w_value in output[0].dct_w.iteritems():
            assert key in ['hash', 'hash_type']

    def test_load_phar(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar');
        $p['foo.txt'] = 'Foo';
        Phar::loadPhar('/tmp/newphar.phar', 'test.phar');
        echo file_get_contents('phar://test.phar/foo.txt');
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.phar');
        ''')
        assert self.space.str_w(output[0]) == 'Foo'

    def test_set_alias(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar');
        $p['foo.txt'] = 'Foo';
        $p->setAlias('test.phar');
        echo file_get_contents('phar://test.phar/foo.txt');
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.phar');
        ''')
        assert self.space.str_w(output[0]) == 'Foo'

    def test_uncompressallfiles(self):       # XXX: Doesn't pass on first runs
        output = self.run('''
        $p = new Phar('/tmp/decomp_phar1.phar', 0, 'decomp_phar1.phar');
        $p['myfile1.txt'] = 'Foo.';
        $p['myfile2.txt'] = 'Bar.';
        $p->compressFiles(Phar::GZ);
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
//        unset($p);
//        Phar::unlinkArchive('/tmp/decomp_phar1.phar');
        ''')
        assert len(output) == 12
        i = 0
        while i < 6:
            assert output[i] == self.space.w_True
            assert output[i+1] == self.space.w_True
            assert output[i+2] == self.space.w_False
            i += 3
        while i < 12:
            assert output[i] == self.space.w_False
            i += 1

    def test_decompress(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar', 0, 'newphar.phar');
        $p['myfile1.txt'] = 'Foo';
        $p['myfile2.txt'] = 'Bar';
        $p1 = $p->compress(Phar::GZ);
        echo $p1->isCompressed();
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.phar');

        $p2 = $p1->decompress();
        echo get_class($p2);
        echo $p2->isCompressed();

        unset($p1);
        unset($p2);
        Phar::unlinkArchive('/tmp/newphar.phar');
        Phar::unlinkArchive('/tmp/newphar.phar.gz');
        ''')
        assert self.space.int_w(output[0]) == 4096
        assert self.space.str_w(output[1]) == 'Phar'
        assert output[2] == self.space.w_False

    def test_stub(self):
        output = self.run('''
        try {
            $p = new Phar('/tmp/brandnewphar.phar', 0, 'brandnewphar.phar');
            $p['a.php'] = '<?php echo "Hello";';
            $p->setStub('<?php var_dump("First"); Phar::mapPhar("brandnewphar.phar"); __HALT_COMPILER(); ?>');
            include 'phar://brandnewphar.phar/a.php';
            echo $p->getStub();
            $p['b.php'] = '<?php echo "World";';
            $p->setStub('<?php var_dump("Second"); Phar::mapPhar("brandnewphar.phar"); __HALT_COMPILER(); ?>');
            include 'phar://brandnewphar.phar/b.php';
            echo $p->getStub();
            unset($p);
            Phar::unlinkArchive('/tmp/brandnewphar.phar');
        } catch (Exception $e) {
            echo 'Write operations failed on brandnewphar.phar: ', $e;
        }
        ''')
        assert len(output) == 4
        assert self.space.str_w(output[0]) == 'Hello'
        assert self.space.str_w(output[1]) == '<?php var_dump("First"); Phar::mapPhar("brandnewphar.phar"); __HALT_COMPILER(); ?>\r\n'
        assert self.space.str_w(output[2]) == 'World'
        assert self.space.str_w(output[3]) == '<?php var_dump("Second"); Phar::mapPhar("brandnewphar.phar"); __HALT_COMPILER(); ?>\r\n'

    def test_is_file_format(self):
        output = self.run('''
        $p = new Phar('/tmp/newphar.phar', 0, 'newphar.phar');
        $p['myfile1.txt'] = 'Foo';
        echo $p->isFileFormat(Phar::PHAR);
        echo $p->isFileFormat(Phar::TAR);
        echo $p->isFileFormat(Phar::ZIP);
        unset($p);
        Phar::unlinkArchive('/tmp/newphar.phar');
        ''')
        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_False
        assert output[2] == self.space.w_False


