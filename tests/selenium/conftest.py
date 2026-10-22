import os

import pytest
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080").rstrip("/")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password123")


@pytest.fixture(scope="session")
def base():
    return FRONTEND_URL


@pytest.fixture
def driver():
    """Headless Chrome (Selenium Manager fetches the driver). Set BROWSER=firefox or
    SELENIUM_REMOTE_URL=http://grid:4444/wd/hub to use another browser / a Grid."""
    browser = os.getenv("BROWSER", "chrome").lower()
    if browser == "firefox":
        opts = webdriver.FirefoxOptions()
        opts.add_argument("-headless")
    else:
        opts = webdriver.ChromeOptions()
        for a in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1366,900"):
            opts.add_argument(a)
    remote = os.getenv("SELENIUM_REMOTE_URL")
    d = webdriver.Remote(command_executor=remote, options=opts) if remote else (
        webdriver.Firefox(options=opts) if browser == "firefox" else webdriver.Chrome(options=opts))
    d.implicitly_wait(0)
    yield d
    d.quit()


@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 15)
