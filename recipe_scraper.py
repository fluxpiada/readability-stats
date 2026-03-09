from recipe_scrapers import scrape_me

url = "https://www.greedygourmet.com/peruvian-ceviche-tigers-milk/"
scraper = scrape_me(url)

print("TITLE:")
print(scraper.title())
print()

print("INGREDIENTS:")
for i in scraper.ingredients():
    print("-", i)
print()

print("INSTRUCTIONS:")
print(scraper.instructions())
