import uuid

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from conftest import ADMIN_EMAIL, ADMIN_PASSWORD

pytestmark = pytest.mark.selenium


def login(driver, wait, base, email=ADMIN_EMAIL, password=ADMIN_PASSWORD):
    driver.get(f"{base}/login")
    wait.until(EC.visibility_of_element_located((By.ID, "email"))).send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "form[data-testid=login-form] button[type=submit]").click()


def test_protected_page_redirects_anonymous_to_login(driver, wait, base):
    driver.get(f"{base}/todos")
    wait.until(EC.url_contains("/login"))
    assert driver.find_element(By.CSS_SELECTOR, "h1").text == "Sign in"


def test_invalid_login_shows_error(driver, wait, base):
    login(driver, wait, base, password="definitely-wrong")
    err = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".form-page__error")))
    assert "Invalid email or password" in err.text
    assert "/login" in driver.current_url


def test_login_then_logout(driver, wait, base):
    login(driver, wait, base)
    wait.until(EC.url_contains("/todos"))
    assert ADMIN_EMAIL in wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid=nav-user]"))).text
    driver.find_element(By.CSS_SELECTOR, ".site-nav__logout").click()
    wait.until(EC.url_contains("/login"))
    driver.get(f"{base}/todos")
    wait.until(EC.url_contains("/login"))


def test_create_edit_complete_delete_todo(driver, wait, base):
    title = f"selenium-{uuid.uuid4().hex[:6]}"
    login(driver, wait, base)
    wait.until(EC.url_contains("/todos"))

    driver.get(f"{base}/add")
    wait.until(EC.visibility_of_element_located((By.ID, "title"))).send_keys(title)
    driver.find_element(By.ID, "desc").send_keys("created via selenium")
    driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

    item = (By.XPATH, f"//li[contains(@class,'todos-page__item')][.//h3[text()='{title}']]")
    wait.until(EC.visibility_of_element_located(item))

    driver.find_element(*item).find_element(By.LINK_TEXT, "Edit").click()
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type=checkbox]"))).click()
    driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
    wait.until(EC.visibility_of_element_located(
        (By.XPATH, f"//li[contains(@class,'todos-page__item--completed')][.//h3[text()='{title}']]")))

    driver.find_element(*item).find_element(By.XPATH, ".//button[text()='Delete']").click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Yes, Delete']"))).click()
    wait.until(EC.invisibility_of_element_located(item))
