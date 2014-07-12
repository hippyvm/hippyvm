

def pytest_addoption(parser):
    group = parser.getgroup("pypy options")
    group.addoption('-A', '--runappdirect', action="store_true",
                    default=False, dest="runappdirect",
                    help="run applevel tests directly on the php interpreter")


def pytest_configure(config):
    global option
    option = config.option
