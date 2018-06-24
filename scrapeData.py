def scrape_data(maxrows=100, filename='funds_100.csv'):

    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver import ActionChains
    from selenium.webdriver import TouchActions
    from selenium.webdriver.support import expected_conditions as ec
    from bs4 import BeautifulSoup
    import csv
    import time
    import math

    def grab_tab(tag, tab):
        print("Looking for %s tab: %s" % (tag, tab))
        tab_element = driver.find_element_by_id(tab)
        tab_actions = ActionChains(driver)
        tab_actions.move_to_element(tab_element)
        tab_actions.click()
        tab_actions.perform()
        tab_actions = TouchActions(driver)
        tab_actions.tap(tab_element)
        tab_actions.perform()
        return driver.page_source

    url_core = "https://www.fidelity.co.uk/investing/investment-finder#?investmentType=funds"
    url_params1 = "&filtersSelectedValue=%7B%7D&sortField=legalName&sortOrder=asc"
    url_params2 = "subUniverseId=MFEI&universeId=FOGBR$$ALL_3521"

    if maxrows > 100:
        pagerows = 500
    else:
        pagerows = maxrows
    pages = int(maxrows / pagerows)
    print("scrape_data: grabbing %d fund details into %s (in %d chunks)" % (maxrows, filename, pages))
    driver = webdriver.Chrome()
    driver.set_page_load_timeout(120)
    driver.get(url_core + "&page=1&perPage=10" + url_params1 + url_params2)
    print("  GET completed, waiting for presence of Cookie")
    try:
        WebDriverWait(driver, 20).until(
            ec.presence_of_element_located((By.ID, "cookieMgn"))
        )
    finally:
        print("  Waiting for cookie to go...")
        try:
            WebDriverWait(driver, 20).until(
                ec.invisibility_of_element_located((By.ID, "cookieMgn"))
            )
        finally:
            cookieC = driver.find_element_by_id("cookieMgn")

    fund_containers = []
    overview_containers = []
    performance_containers = []
    charges_containers = []
    annual_perf_containers = []

    for p in range(pages):
        url_perpage = "&page=%d&perPage=%d" % (p+1, pagerows)
        url_grab = url_core + url_perpage + url_params1 + url_params2

        # GRAB the real OVERVIEW page with fund count requested
        print("  Getting the URL again: %s" % url_grab)
        driver.get(url_grab)
        ajax_wait = math.sqrt(pagerows)
        print("  ...now wait for AJAX load to finish (%d secs for %d rows)" % (ajax_wait, pagerows))
        time.sleep(ajax_wait)

        # GRAB the individual tabs
        overview_page = grab_tab('OVERVIEW', 'ec-screener-loader-fidelity-funds-view-tabs-tab0')
        performance_page = grab_tab('PERFORMANCE', 'ec-screener-loader-fidelity-funds-view-tabs-tab1')
        charges_page = grab_tab('CHARGES', 'ec-screener-loader-fidelity-funds-view-tabs-tab2')
        annual_perf_page = grab_tab('ANNUAL PERFORMANCE', 'ec-screener-loader-fidelity-funds-view-tabs-tab3')

        soup_o = BeautifulSoup(overview_page, "html.parser")
        soup_p = BeautifulSoup(performance_page, "html.parser")
        soup_c = BeautifulSoup(charges_page, "html.parser")
        soup_ap = BeautifulSoup(annual_perf_page, "html.parser")

        fund_containers = fund_containers + soup_o.find_all('a', class_='ec-table__investment-link')
        overview_containers = overview_containers + soup_o.find_all('div', class_='ec-table__cell-content ng-binding')
        performance_containers = performance_containers + soup_p.find_all('div', class_='ec-table__cell-content ng-binding')
        charges_containers = charges_containers + soup_c.find_all('div', class_='ec-table__cell-content ng-binding')
        annual_perf_containers = annual_perf_containers + soup_ap.find_all('div', class_='ec-table__cell-content ng-binding')

        print("  >>> Page %d, now have %s fund details" % (p+1, len(fund_containers)))

    # QUIT the BROWSER
    print("  quitting browser")
    driver.quit()

    dp = 0
    hdrmsg = ["Fund Name", "NegDisc(O)", "Yield", "OngoingCharge(O)", "Asset class", "NegDisc(P)",
              "Y-5", "Y-4", "Y-3", "Y-2", "Y-1", "MinInvest", "InitialCharge", "FundProviderBuyCharge",
              "FundProvideSellCharge", "OngoingCharge(C)", "NegDisc(C)", "YTD Return", "1Y Annualised",
              "3Y Annualised", "5Y Annualised", "10Y Annualised"]
    fundrows = [hdrmsg]
    for i in fund_containers:
        rowmsg = []
        rowmsg.append(i.string)
        # OVERVIEW datapoints
        rowmsg.append(overview_containers[(dp * 4)].string.strip())
        rowmsg.append(overview_containers[(dp * 4) + 1].string.strip())
        rowmsg.append(overview_containers[(dp * 4) + 2].string.strip())
        rowmsg.append(overview_containers[(dp * 4) + 3].string.strip())
        # PERFORMANCE datapoints
        rowmsg.append(performance_containers[(dp * 6)].string.strip())
        rowmsg.append(performance_containers[(dp * 6) + 1].string.strip())
        rowmsg.append(performance_containers[(dp * 6) + 2].string.strip())
        rowmsg.append(performance_containers[(dp * 6) + 3].string.strip())
        rowmsg.append(performance_containers[(dp * 6) + 4].string.strip())
        rowmsg.append(performance_containers[(dp * 6) + 5].string.strip())
        # CHARGES datapoints
        rowmsg.append(charges_containers[(dp * 6)].string.strip())
        rowmsg.append(charges_containers[(dp * 6) + 1].string.strip())
        rowmsg.append(charges_containers[(dp * 6) + 2].string.strip())
        rowmsg.append(charges_containers[(dp * 6) + 3].string.strip())
        rowmsg.append(charges_containers[(dp * 6) + 4].string.strip())
        rowmsg.append(charges_containers[(dp * 6) + 5].string.strip())
        # ANNUALISED PERFORMANCE datapoints
        rowmsg.append(annual_perf_containers[(dp * 5)].string.strip())
        rowmsg.append(annual_perf_containers[(dp * 5) + 1].string.strip())
        rowmsg.append(annual_perf_containers[(dp * 5) + 2].string.strip())
        rowmsg.append(annual_perf_containers[(dp * 5) + 3].string.strip())
        rowmsg.append(annual_perf_containers[(dp * 5) + 4].string.strip())

        new_rowmsg = [x if x != '–' else '0.00' for x in rowmsg]
        dp = dp + 1
        fundrows.append(new_rowmsg)
        # print(new_rowmsg)

    print("  ==FUNDROWS: %d" % len(fundrows))

    print("  ==WRITING TO FILE==")
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(fundrows)

    return
