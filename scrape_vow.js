const puppeteer = require('puppeteer');
const cheerio = require('cheerio');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://offene-werkstaetten.org/en/workshop-search', { waitUntil: 'networkidle2' });

  const html = await page.content();
  const $ = cheerio.load(html);

  const workshops = [];
  $('#workshops-wrapper > div').each((i, el) => {
    workshops.push({
      index: i + 1,
      name: $(el).find('a.workshop-name').text().trim(),
      profileUrl: 'https://offene-werkstaetten.org' + $(el).find('a.workshop-name').attr('href'),
      address: $(el).find('p.address').clone().find('a').remove().end().text().trim(),
      website: $(el).find('p.address a').attr('href') || null,
      categories: $(el).find('.categories-wrapper img').map((_, img) => $(img).attr('title')).get()
    });
  });

  console.log(JSON.stringify(workshops, null, 2));
  await browser.close();
})();
