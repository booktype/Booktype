from booktype import constants
from booktype.utils import config
from booktype.tests import TestCase


class ConstantsTestCase(TestCase):
    def setUp(self):
        self.constants = constants
        self.config = config

    def test_constants(self):
        self.assertEqual(self.constants.PUBLISH_OPTIONS, self.config.get_configuration('PUBLISH_OPTIONS'))
        self.assertEqual(self.constants.OBJAVI_URL, self.config.get_configuration('OBJAVI_URL'))
        self.assertEqual(self.constants.ESPRI_URL, self.config.get_configuration('ESPRI_URL'))
        self.assertNotEqual(self.constants.THIS_BOOKI_SERVER, self.config.get_configuration('THIS_BOOKI_SERVER'))
        self.assertEqual(self.constants.CREATE_BOOK_VISIBLE, self.config.get_configuration('CREATE_BOOK_VISIBLE'))
        self.assertEqual(self.constants.CREATE_BOOK_LICENSE, self.config.get_configuration('CREATE_BOOK_LICENSE'))
        self.assertEqual(self.constants.FREE_REGISTRATION, self.config.get_configuration('FREE_REGISTRATION'))
        self.assertEqual(self.constants.ADMIN_CREATE_BOOKS, self.config.get_configuration('ADMIN_CREATE_BOOKS'))
        self.assertEqual(self.constants.ADMIN_IMPORT_BOOKS, self.config.get_configuration('ADMIN_IMPORT_BOOKS'))
        self.assertEqual(self.constants.BOOKTYPE_MAX_USERS, self.config.get_configuration('BOOKTYPE_MAX_USERS'))
        self.assertEqual(self.constants.BOOKTYPE_MAX_BOOKS, self.config.get_configuration('BOOKTYPE_MAX_BOOKS'))
        self.assertEqual(self.constants.BOOKTYPE_CSS_BOOK, self.config.get_configuration('BOOKTYPE_CSS_BOOK'))
        self.assertEqual(self.constants.BOOKTYPE_CSS_BOOKJS, self.config.get_configuration('BOOKTYPE_CSS_BOOKJS'))
        self.assertEqual(self.constants.BOOKTYPE_CSS_EBOOK, self.config.get_configuration('BOOKTYPE_CSS_EBOOK'))
        self.assertEqual(self.constants.BOOKTYPE_CSS_PDF, self.config.get_configuration('BOOKTYPE_CSS_PDF'))
        self.assertEqual(self.constants.BOOKTYPE_CSS_ODT, self.config.get_configuration('BOOKTYPE_CSS_ODT'))
