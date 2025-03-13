import subprocess
import time

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_onboarding_modal():
    """
    Simplified test to ensure the page actually loads in Selenium.
    """
    process = subprocess.Popen(
        ["python", "-m", "my_digital_being.server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Give the server time to start
    time.sleep(5)

    try:
        # Start the Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)

        # Navigate to server's root URL
        driver.get("http://localhost:8000")

        # Wait for the page to load and find the Setup Wizard button
        setup_wizard_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "open-setup-wizard"))
        )

        # Check if it's there
        assert setup_wizard_button.is_displayed(), "Setup wizard button should be visible"

    finally:
        # Clean up resources
        try:
            driver.quit()
        except:
            pass

        process.terminate()
        process.wait()
        stdout, stderr = process.communicate()
        print("Server stdout:", stdout.decode())
        print("Server stderr:", stderr.decode())
