"""All of the application-level options."""
from tornado.options import define, options, parse_command_line

__all__ = ('options', 'parse_command_line')

define('db_host', default='localhost')
define('db_port', default=5432)
define('db_database', default='demo')
define('db_schema', default='demo')
define('db_user', default='postgres')
define('db_password', default='password')
