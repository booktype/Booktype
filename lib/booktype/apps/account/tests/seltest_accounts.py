from django.core.urlresolvers import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException


class MySeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        super(MySeleniumTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(MySeleniumTests, cls).tearDownClass()

    def test_login(self):
        self.selenium.get('%s%s' % (self.live_server_url, reverse('accounts:signin')))
        signin_input = self.selenium.find_element_by_id('formsignin')
        username_input = signin_input.find_element_by_name("username")
        username_input.send_keys('myuser')
        password_input = signin_input.find_element_by_name("password")
        password_input.send_keys('secret')

        signin_input.find_element_by_xpath('//input[@value="Sign In"]').click()

        noSuchUser = signin_input.find_element_by_class_name("no-such-user")
        self.assertRaises(NoSuchElementException, noSuchUser.find_element_by_class_name, "template")
        self.assertEquals(noSuchUser.text, 'User does not exist.')

    def test_register_missing_username(self):
        self.selenium.get('%s%s' % (self.live_server_url, reverse('accounts:signin')))
        register_form = self.selenium.find_element_by_id('formregister')

        self.selenium.find_element_by_xpath('//input[@value="CREATE ACCOUNT"]').click()

        noSuchUser = self.selenium.find_element_by_class_name("no-such-user")
        self.assertRaises(NoSuchElementException, noSuchUser.find_element_by_class_name, 'template')
        self.assertEquals(register_form.find_element_by_class_name('missing-username').text, 'Missing username!')

    def test_register_missing_email(self):
        self.selenium.get('%s%s' % (self.live_server_url, reverse('accounts:signin')))
        register_form = self.selenium.find_element_by_id('formregister')
        username_input = register_form.find_element_by_name("username")
        username_input.send_keys('myuser')

        self.selenium.find_element_by_xpath('//input[@value="CREATE ACCOUNT"]').click()

        noSuchUser = self.selenium.find_element_by_class_name("missing-email")
        self.assertRaises(NoSuchElementException, noSuchUser.find_element_by_class_name, 'template')
        self.assertEquals(register_form.find_element_by_class_name('missing-email').text, 'Missing e-mail!')

    def test_register_missing_password(self):
        self.selenium.get('%s%s' % (self.live_server_url, reverse('accounts:signin')))
        register_form = self.selenium.find_element_by_id('formregister')
        username_input = register_form.find_element_by_name("username")
        username_input.send_keys('myuser')
        email_input = register_form.find_element_by_name("email")
        email_input.send_keys('email@email.com')

        self.selenium.find_element_by_xpath('//input[@value="CREATE ACCOUNT"]').click()

        missingPassword = self.selenium.find_element_by_class_name("missing-password")
        self.assertRaises(NoSuchElementException, missingPassword.find_element_by_class_name, 'template')
        self.assertEquals(register_form.find_element_by_class_name('missing-password').text, 'Missing password!')

    def test_register_missing_fullname(self):
        self.selenium.get('%s%s' % (self.live_server_url, reverse('accounts:signin')))
        register_form = self.selenium.find_element_by_id('formregister')
        username_input = register_form.find_element_by_name("username")
        username_input.send_keys('myuser')
        email_input = register_form.find_element_by_name("email")
        email_input.send_keys('email@email.com')
        password_input = register_form.find_element_by_name("password")
        password_input.send_keys('secret')

        self.selenium.find_element_by_xpath('//input[@value="CREATE ACCOUNT"]').click()

        missingFullname = self.selenium.find_element_by_class_name("missing-fullname")
        self.assertRaises(NoSuchElementException, missingFullname.find_element_by_class_name, 'template')
        self.assertEquals(register_form.find_element_by_class_name('missing-fullname').text, 'Please provide your real name.')

    def test_register_short_password(self):
        self.selenium.get('%s%s' % (self.live_server_url, reverse('accounts:signin')))
        register_form = self.selenium.find_element_by_id('formregister')
        username_input = register_form.find_element_by_name("username")
        username_input.send_keys('myuser')
        email_input = register_form.find_element_by_name("email")
        email_input.send_keys('email@email.com')
        password_input = register_form.find_element_by_name("password")
        password_input.send_keys('123')
        fname_input = register_form.find_element_by_name("fullname")
        fname_input.send_keys('Full Name')

        self.selenium.find_element_by_xpath('//input[@value="CREATE ACCOUNT"]').click()

        invalidPassword = self.selenium.find_element_by_class_name("invalid-password")
        self.assertRaises(NoSuchElementException, invalidPassword.find_element_by_class_name, 'template')
        self.assertEquals(invalidPassword.text, 'Password must be 6 characters or more!')
