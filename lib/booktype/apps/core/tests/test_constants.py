import unittest

class ConstantsTestCase(unittest.TestCase):
    def setUp(self):
        from booktype.utils import config
        from booktype import constants
        self.c = constants
        self.cfg = config

    def test_constants(self):
        self.assertEqual(self.c.PUBLISH_OPTIONS, self.cfg.get_configuration('PUBLISH_OPTIONS'))
        self.assertEqual(self.c.OBJAVI_URL, self.cfg.get_configuration('OBJAVI_URL'))
        self.assertEqual(self.c.ESPRI_URL, self.cfg.get_configuration('ESPRI_URL'))
        self.assertNotEqual(self.c.THIS_BOOKI_SERVER, self.cfg.get_configuration('THIS_BOOKI_SERVER'))
        self.assertEqual(self.c.CREATE_BOOK_VISIBLE, self.cfg.get_configuration('CREATE_BOOK_VISIBLE'))
        self.assertEqual(self.c.CREATE_BOOK_LICENSE, self.cfg.get_configuration('CREATE_BOOK_LICENSE'))
        self.assertEqual(self.c.FREE_REGISTRATION, self.cfg.get_configuration('FREE_REGISTRATION'))
        self.assertEqual(self.c.ADMIN_CREATE_BOOKS, self.cfg.get_configuration('ADMIN_CREATE_BOOKS'))
        self.assertEqual(self.c.ADMIN_IMPORT_BOOKS, self.cfg.get_configuration('ADMIN_IMPORT_BOOKS'))
        self.assertEqual(self.c.BOOKTYPE_MAX_USERS, self.cfg.get_configuration('BOOKTYPE_MAX_USERS'))
        self.assertEqual(self.c.BOOKTYPE_MAX_BOOKS, self.cfg.get_configuration('BOOKTYPE_MAX_BOOKS'))
        self.assertEqual(self.c.BOOKTYPE_CSS_BOOK, self.cfg.get_configuration('BOOKTYPE_CSS_BOOK'))
        self.assertEqual(self.c.BOOKTYPE_CSS_BOOKJS, self.cfg.get_configuration('BOOKTYPE_CSS_BOOKJS'))
        self.assertEqual(self.c.BOOKTYPE_CSS_EBOOK, self.cfg.get_configuration('BOOKTYPE_CSS_EBOOK'))
        self.assertEqual(self.c.BOOKTYPE_CSS_PDF, self.cfg.get_configuration('BOOKTYPE_CSS_PDF'))
        self.assertEqual(self.c.BOOKTYPE_CSS_ODT, self.cfg.get_configuration('BOOKTYPE_CSS_ODT'))


