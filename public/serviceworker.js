const CACHE_NAME = 'zotmeal-cache'
const assets = [
    "/",
]

self.addEventListener("install", installEvent => {
    console.log("installed!")
    installEvent.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            cache.addAll(assets)
        })
    )
})

self.addEventListener("fetch", fetchEvent => {
    console.log(fetchEvent);
    fetchEvent.respondWith(
        caches.match(fetchEvent.request).then(res => {
            return res || fetch(fetchEvent.request)
        })
    )
})