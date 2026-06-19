
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "proxy.example.com",
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
                    username: "proxy-user",
                    password: "proxy-password"
                }
            };
        },
        {urls: ["<all_urls>"]},
        ['blocking']
    );
    
