import time
import random
from playwright.sync_api import sync_playwright, Error as PlaywrightError

url = input('Url: ')


def get_facebook_reels(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)

        input('Zaloguj się na przeglądarce która się otworzyła i upewnij, że jesteś na stronie reelsów profilu który chcesz pobrać.\n'
              'Jeśli to zrobiłeś, kliknij ENTER w tym oknie konsoli')
        print('Zbieranie linków... (Najprawdopodobniej zajmie to dużo czasu, nie zamykaj przeglądarki która się otworzyła)')

        try:
            page.wait_for_load_state("domcontentloaded", timeout=10000)
        except PlaywrightError:
            pass

        if page.url != url:
            page.goto(url)
            page.wait_for_load_state("domcontentloaded")

        all_links = set()
        no_new_links_count = 0

        while no_new_links_count < 15:
            try:
                links = page.locator("a[href*='/reel/']").evaluate_all(
                    "elements => elements.map(e => e.href)"
                )

                count_before = len(all_links)
                for index in range(len(links)):
                    link = links[index]
                    if link not in all_links:
                        print(f'{index+1}. {link[:link.find('/?s=fb_shorts')]}')

                all_links.update(links)

                if len(all_links) > count_before:
                    no_new_links_count = 0
                else:
                    no_new_links_count += 1

                page.evaluate("window.scrollBy(0, 800)")
                time.sleep(random.uniform(1.5, 3.5))

            except PlaywrightError as e:
                if "Execution context was destroyed" in str(e):
                    time.sleep(2)
                    continue
                else:
                    raise e

        with open('reels_fetcher_output.txt', 'w') as file:
            file.write(f'# url: "{url}"\n'
                       f'# Control+a Control+c wszystko i wklej do pliku .txt do pobierania grupowego\n')
            for link in all_links:
                if '/?s=fb_shorts' in link:
                    link = link[:link.find('/?s=fb_shorts')]
                if link == 'https://www.facebook.com/reel/?s=tab':

                    continue
                file.write(f'{link}\n')

        print(f"\nLinków łącznie: {len(all_links)}")

        browser.close()


get_facebook_reels(url)

print('Linki zapisane w formacie gotowym do pobierania przez yt-dl, w pliku reels_fetcher_output.txt w tym samym folderze co .exe tego programu\n'
      'Good luck nigga')
input(f'Kliknij Enter żeby zakończyć')