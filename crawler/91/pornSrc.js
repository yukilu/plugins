const fs = require('fs');
const http = require('http');
const cheerio = require('cheerio');

console.log('pornSrc.js begins...');
const settingFile = 'porn/setting.json';
const setting = readFileSync(settingFile, 'json');
const { chosen, series, DURATION, ITEM_AMOUNT, MAX_AMOUNT, domain } = setting;
const chosenSeries = series[chosen];
const { title, pageSrcIndex } = chosenSeries;

if (ITEM_AMOUNT > MAX_AMOUNT || ITEM_AMOUNT < 1)
    throw new Error(`ITEM_AMOUT can\'t be less than 1 or more than ${MAX_AMOUNT}!`);

let pageIndex = pageSrcIndex;
const hrefFile = `porn/${title}Href${pageIndex === 1 ? '' : pageIndex}.txt`;
const srcFile = `porn/${title}Src.txt`;
const tempFile = `porn/${title}TempSrc.txt`;

const hrefTxts = [];
const hrefs = readFileSync(hrefFile, 'json');
let targetHrefs = hrefs.filter(href => !href.done);
hrefTxts.push(hrefs);

let nextHrefFile;
try {
    while (targetHrefs.length < ITEM_AMOUNT) {
        nextHrefFile = `porn/${title}Href${++pageIndex}.txt`;
        const nextHrefs = readFileSync(nextHrefFile, 'json');
        const filteredHrefs = nextHrefs.filter(href => !href.done);
        hrefTxts.push(nextHrefs);
        targetHrefs = targetHrefs.concat(filteredHrefs);
    }
} catch(e) {
    // console.log(e);
    console.log(`${nextHrefFile} not exist, readFileSync error!`);
    --pageIndex;
}

const initialTargetHrefsLength = targetHrefs.length;
if (!initialTargetHrefsLength)
    throw new Error('targetHref can\'t be empty!');
else if (initialTargetHrefsLength > ITEM_AMOUNT)
    targetHrefs = targetHrefs.slice(0, ITEM_AMOUNT);
const targetHrefsLength = targetHrefs.length;

console.log(`domain=${domain}, title=${title}, pageIndex=[${pageSrcIndex} -> ${pageIndex}], DURATION=${DURATION}`);
console.log(`ITEM_AMOUNT=${ITEM_AMOUNT}, targetHrefsLength=${targetHrefsLength}`);

let notGetCounter = 0;
const promises = targetHrefs.map(function (href, index) {
    let url = href.href;
    if (url.indexOf('http') === -1)
        url = domain + url;
    return getUrl(url, index * DURATION).then(function ($) {
        const node = $('source')[0];
        const src = node ? node.attribs.src : null;
        if (src) {
            href.done = true;
            writeFile(tempFile, `${src}\r\n`, 'a').catch(errorHandler);
        } else
            ++notGetCounter;
        console.log(`itemIndex=${href.itemIndex}, pageIndex=${title} ${href.pageIndex}, count=${index + 1}`);
        console.log(src);
        return src;
    }, err => {
        ++notGetCounter;
        console.log(`itemIndex=${href.itemIndex}, pageIndex=${title} ${href.pageIndex}, count=${index + 1}`);
        console.log('network error', err);
    });
});
// const promises = hrefs.slice(item, itemIndex + ITEM_AMOUNT).map((href, index) => getUrl(href, index));
Promise.all(promises).then(function (results) {
    if (notGetCounter === targetHrefsLength) {
        console.log('None src got! Setting.json noupdated.');
        return;
    }

    const lastTargetHref = targetHrefs[targetHrefsLength - 1];
    let nextPageSrcIndex;
    if (notGetCounter)  // have null or error
        nextPageSrcIndex = targetHrefs.find(href => !href.done).pageIndex;
    else if (lastTargetHref.itemIndex === 19) // not have null or error, check the pageIndex of the last href item
        nextPageSrcIndex = lastTargetHref.pageIndex + 1;
    else
        nextPageSrcIndex = lastTargetHref.pageIndex;
    
    chosenSeries.pageSrcIndex = nextPageSrcIndex;
    setting.lastSrcModified = new Date().toUTCString();

    hrefTxts.forEach(hrefs => {
        const hrefFile = `porn/${title}Href${hrefs[0].pageIndex}.txt`;
        writeFile(hrefFile, JSON.stringify(hrefs, null, 2)).then(info => console.log(info), errorHandler);
    });
    writeFile(srcFile, results.join('\r\n')).then(info => {
        console.log(info);
        console.log(`Done, got ${targetHrefsLength - notGetCounter} srcs!`);
    }, errorHandler);
    unlink(tempFile).catch(errorHandler);
    writeFile(settingFile, JSON.stringify(setting, null, 2)).then(function(info) {
        console.log(info);
        if (nextPageSrcIndex > pageSrcIndex)
            console.log(`pageSrcIndex has updated to ${nextPageSrcIndex}.`);
        else
            console.log('pageSrcIndex noupdated!');
    }, errorHandler);
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