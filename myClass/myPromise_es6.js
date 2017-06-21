class MyPromise {
    constructor(fn) {
        const that = this;
        let successCallback, failCallback;
        let value, error;
        let state = 'PENDING';

        fn(resolve, reject);

        function resolve(v) {
            that.value = value;
            that.state = 'FULFILLED';
            successCallback && successCallback(v);
        }

        function reject(e) {
            that.error = e;
            that.state = 'REJECTED';
            failCallback && failCallback(e);
        }
    }
    then(fulfilled, rejected) {
        let rtn;
        let that = this;
        if (this.state === 'FULFILLED') {
            rtn = fulfilled && fulfilled(this.value);
            if (rtn == undefined || typeof rtn.then !== 'function')
                rtn = new Promise(resolve => { resolve(rtn); });

        }
        else if (this.state === 'REJECTED') {
            rejected && rejected(this.error);
            rtn = new Promise((resolve, reject) => { reject(this.error); });
                
        }
        else { //this.state === 'PENDING'
            rtn = new Promise(function (resolve, reject) {
                that.successCallback = function (v) {
                    let r = fulfilled && fulfilled(v);
                    if (r && r.then === 'function')
                        r.then(v => {
                            resolve(v);
                        }, e => {
                            reject(e);
                        });
                    else
                        resolve(r);
                };
                that.failCallback = function (e) {
                    rejected && rejected(e);
                    reject(e);
                };
            });
        }

        return rtn;
    }
}

let p = new Promise(resolve => {
    setTimeout(() => {
        resolve(0);
    }, 2000);
});

let r = p.then(v => {
    console.log(v);
    return new Promise(resolve => {
        setTimeout(() => {
            resolve(1);
        }, 2000);
    });
}).then(v => {
    console.log(v);
    return new Promise(resolve => {
        setTimeout(() => {
            resolve(2);
        }, 2000);
    });
}).then(v => {
    console.log(v);
    return 3;
}).then(v => {
    console.log(v);
});

console.log(r.constructor);