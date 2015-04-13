from unittest import TestCase

from . import utils


class ValidateHostTestCase(TestCase):
    def test_should_fail_on_empty_allowed_hosts(self):
        allowed_hosts = []
        self.assertFalse(utils.validate_host('', allowed_hosts))

    def test_should_allow_domain_and_subdomains(self):
        allowed_hosts = ['.example.com']
        self.assertTrue(utils.validate_host('example.com', allowed_hosts))
        self.assertTrue(utils.validate_host('www.example.com', allowed_hosts))
        self.assertTrue(utils.validate_host('ftp.example.com', allowed_hosts))

    def test_should_match_anything_on_asterisk(self):
        allowed_hosts = ['*']
        self.assertTrue(utils.validate_host('example.com', allowed_hosts))
        self.assertTrue(utils.validate_host('test.com', allowed_hosts))

    def test_should_match_only_exact(self):
        allowed_hosts = ['example.com']
        self.assertTrue(utils.validate_host('example.com', allowed_hosts))
        self.assertFalse(utils.validate_host('www.example.com', allowed_hosts))
