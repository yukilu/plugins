const fs = require('fs');
const http = require('http');
const cheerio = require('cheerio');

console.log('pornSrc.js begins...');
const settingFile = 'porn/setting.json';
const setting = readFileSync(settingFile, 'json');
const { chosen, series, DURATION, ITEM_AMOUNT } = setting;
const chosenSeries = series[chosen];
const { title, pageSrcIndex, itemIndex } = chosenSeries;

const pageIndex = pageSrcIndex;
const strIndex = pageIndex === 1 ? '' : pageIndex;
const hrefFile = `porn/${title}Href${strIndex}.txt`;
const srcFile = `porn/${title}Src${strIndex}.txt`;
const tempFile = `porn/${title}TempSrc${strIndex}.txt`;

let firstNullIndex = -1;
let endItemIndex = itemIndex + ITEM_AMOUNT - 1;
const hrefs = readFileSync(hrefFile, 'json');
const lastHrefIndex = hrefs.length - 1;
const meetEnd = endItemIndex >= lastHrefIndex;
if (meetEnd)
    endItemIndex = lastHrefIndex;
const hrefsSliced = hrefs.slice(itemIndex, endItemIndex + 1);

console.log(`title=${title}, pageIndex=${pageIndex}, startIndex=${itemIndex}, DURATION=${DURATION}, ITEM_AMOUNT=${ITEM_AMOUNT}`);

const promises = hrefsSliced.map(function (href, index) {
    return getUrl(href, index * DURATION).then(function ($) {
        const node = $('source')[0];
        const src = node ? node.attribs.src : null;
        if (src)
            writeFile(tempFile, `${src}\r\n`, 'a').catch(errorHandler);
        else if (firstNullIndex === -1)
            firstNullIndex = itemIndex + index;
        console.log(`itemIndex=${itemIndex + index}, pageIndex=${title} ${pageIndex}, count=${index + 1}`);
        console.log(src);
        return src;
    }, errorHandler);
});
// const promises = hrefs.slice(item, itemIndex + ITEM_AMOUNT).map((href, index) => getUrl(href, index));
Promise.all(promises).then(results => {
    const getAtLeastOneSrc = firstNullIndex !== itemIndex;
    const getAtLeastOneNull = firstNullIndex !== -1; 

    if (getAtLeastOneNull)
        chosenSeries.itemIndex = firstNullIndex;
    else if (meetEnd) {
        ++chosenSeries.pageSrcIndex;
        chosenSeries.itemIndex = 0;
    }
    else
        chosenSeries.itemIndex = endItemIndex + 1;
    
    setting.lastSrcModified = new Date().toUTCString();
    if (getAtLeastOneSrc) {
        writeFileSync(srcFile, results.join('\r\n'));
        unlink(tempFile).catch(errorHandler);
        writeFileSync(settingFile, JSON.stringify(setting, null, 2));
        console.log('Done!');
    } else
        console.log('None src got!');

    
    if (!getAtLeastOneNull && meetEnd)
        console.log(`pageSrcIndex has updated to ${chosenSeries.pageSrcIndex}.`);
    else
        console.log('pageSrcIndex noupdated!');
    
    if (atLeastGetOneSrc)
        console.log(`itemIndex has updated to ${chosenSeries.itemIndex}.`);
    else
        console.log('itemIndex noupdated!')
}, errorHandler);

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
            // myGet(url, res => {
            //     console.log(`GET ${url} end.`);
            //     resolve(res);
            // });
        }, time * 1000);
    });
}

function readFile(file) {
    return new Promise((resolve, reject) => {
        fs.readFile(file, (err, data) => {
            if (err)
                reject(err);
            else
                resolve(data);
        });
    });
}

function writeFile(file, data, flag = 'w') {
    return new Promise((resolve, reject) => {
        fs.writeFile(file, data, { flag }, err => {
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

function unlink(file) {
    return new Promise((resolve, reject) => {
        fs.unlink(file, err => {
            if (err)
                reject(err);
            else
                resolve(`unlink ${file} success`);
        });
    });
}

function errorHandler(error) {
    console.log('error', error);
}

function myGet(url, callback) {
    setTimeout(() => {
        callback(url);
    }, rand(2000, 8000));
}

function rand(start, end) {
    return start + Math.floor(Math.random() * (end - start));
}