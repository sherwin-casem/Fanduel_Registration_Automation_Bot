
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "gate.decodo.com",
                port: parseInt(10001)
            },
            bypassList: ["localhost"]
        }
    };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    chrome.webRequest.onAuthRequired.addListener(
        function(details) {
            return {
                authCredentials: {
                    username: "user-sph94wqr63-country-ca-city-toronto",
                    password: "7t+zeL4Fkw1oCaxjP6"
                }
            };
        },
        {urls: ["<all_urls>"]},
        ['blocking']
    );
    