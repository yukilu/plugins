const fs = require('fs');
const http = require('http');
const cheerio = require('cheerio');

const settingFile = 'porn/setting.json';

const setting = readFileSync(settingFile, 'json');
const { chosen, series, DURATION, PAGE_AMOUNT } = setting;
const chosenSeries = series[chosen];
const { title, pageHrefIndex, baseUrl } = chosenSeries;

let promises = [];
const pageIndex = pageHrefIndex;
const endPageIndex = pageIndex + PAGE_AMOUNT;
for (let i = pageIndex; i < endPageIndex; i++)
    promises.push(getHref(i, i - pageIndex));

Promise.all(promises).then(() => {
    chosenSeries.pageHrefIndex = endPageIndex;
    writeFileSync(settingFile, JSON.stringify(setting, null, 2));
    console.log(`Get ${title} page(${pageIndex}~${endPageIndex-1}), all done!`);
}, errorHandler);

function getHref(pageIndex, index = 0) {
    const pageParam = pageIndex === 1 ? '' : `&page=${pageIndex}`;
    const url = `${baseUrl}${pageParam}`;

    const hrefFile = `porn/${title}Href${pageIndex === 1 ? '' : pageIndex}.txt`;

    return getUrl(url, index * DURATION).then(function ($) {
        const hrefs = $('#videobox .imagechannel a, #videobox .imagechannelhd a').map((index, a) => a.attribs.href).toArray();
        writeFileSync(hrefFile, JSON.stringify(hrefs));
        console.log(`${title}[page=${pageIndex}] done!`);
    }, errorHandler);
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
                    console.log(`GOT ${url}.`);
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