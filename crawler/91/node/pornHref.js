const fs = require('fs');
const http = require('http');
const cheerio = require('cheerio');

console.log('pornHref.js begins...');

const settingFile = 'porn/setting.json';
const setting = readFileSync(settingFile, 'json');
const { chosen, series, DURATION, PAGE_AMOUNT, domain, hrefSaveMode } = setting;
const chosenSeries = series[chosen];
const { title, pageHrefIndex, path } = chosenSeries;
const pageIndex = pageHrefIndex;
const finalPageIndex = pageIndex + PAGE_AMOUNT;

console.log(`domain=${domain}, title=${title}, pageIndex=${pageIndex}, DURATION=${DURATION}, PAGE_AMOUNT=${PAGE_AMOUNT}`);

let promises = [];
for (let i = pageIndex; i < finalPageIndex; i++)
    promises.push(getHref(i, i - pageIndex));

Promise.all(promises).then(() => {
    chosenSeries.pageHrefIndex = finalPageIndex;
    setting.lastHrefModified = new Date().toUTCString();
    writeFileSync(settingFile, JSON.stringify(setting, null, 2));
    console.log(`All done, ${title} page[${pageIndex} -> ${finalPageIndex-1}]!`);
}, errorHandler);

function getHref(pageIndex, index = 0) {
    const pageParam = pageIndex === 1 ? '' : `&page=${pageIndex}`;
    const url = `${domain}${path}${pageParam}`;

    const hrefFile = `porn/${title}Href${pageIndex === 1 ? '' : pageIndex}.txt`;

    return getUrl(url, index * DURATION).then(function ($) {
        const hrefs = $('#videobox .imagechannel a, #videobox .imagechannelhd a')
            .map((index, a) => a.attribs.href)
            .toArray()
            .map((href, itemIndex) => {
                if (hrefSaveMode === 0)
                    href = href.replace(domain, '');
                return { href, pageIndex, itemIndex, done: false };
            });
        return writeFile(hrefFile, JSON.stringify(hrefs, null, 2)).then(info => console.log(`${title}[page=${pageIndex}] done!`), errorHandler);
    }, err => {
        console.log(`${title}[page=${pageIndex}] network error!`, err);
    });
}

function getUrl(url, time = 0) {
    return new Promise(function (resolve, reject) {
        setTimeout(() => {
            console.log(`GET ${url} begins...`);
            const request = http.get(url, function (res) {
                let chunks = '';
                res.on('data', chunk => { chunks += chunk; });
                res.on('end', () => {
                    // writeFile('porn.txt', chunks).catch(e => console.log(e));
                    console.log(`GOT ${url}`);
                    const $ = cheerio.load(chunks);
                    resolve($);
                });
            });
            request.on('error', reject);
        }, time * 1000);
    });
}

function writeFile(file, data) {
    return new Promise((resolve, reject) => {
        fs.writeFile(file, data, err => {
            if (err)
                reject(err);
            else
                resolve(`write ${file} success`);
        });
    });
}

function writeFileSync(file, data, flag = 'w') {
    return fs.writeFileSync(file, data, { flag });
}

function readFileSync(file, encoding = 'utf-8') {
    if (encoding === 'json')
        return JSON.parse(fs.readFileSync(file));
    else
        return fs.readFileSync(file, 'utf-8');
}

function errorHandler(error) {
    console.log('error', error);
}