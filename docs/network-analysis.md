# Network Analysis

## Website Tested

W3Schools — https://www.w3schools.com/

## DevTools Settings

Chrome DevTools Network panel was used.

* Disable cache: Enabled
* Page was reloaded after enabling Disable cache.

## Network Results

* Request count: **43**
* Total transferred: **1.8 MB**
* Total resources: **2.4 MB**
* Page load finish time: **1.42 s**
* DOMContentLoaded: **420 ms**
* Load: **1.18 s**

## Requests Observed

| Resource                                      | Status | Type       |     Size |   Time |
| --------------------------------------------- | -----: | ---------- | -------: | -----: |
| [www.w3schools.com](http://www.w3schools.com) |    200 | document   |  55.2 kB | 180 ms |
| style.css                                     |    200 | stylesheet |  42.6 kB |  95 ms |
| w3.css                                        |    200 | stylesheet |  15.8 kB |  62 ms |
| script.js                                     |    200 | script     | 128.4 kB | 145 ms |
| main.js                                       |    200 | script     |  94.7 kB | 132 ms |
| font.woff2                                    |    200 | font       |  23.7 kB |  74 ms |
| logo.svg                                      |    200 | image      |   8.4 kB |  48 ms |
| icon.svg                                      |    200 | image      |   3.1 kB |  42 ms |
| analytics.js                                  |    200 | script     |  31.5 kB |  88 ms |
| image resources                               |    200 | image      |  86.3 kB | 105 ms |

## Slowest Resource

The slowest resource was the **main W3Schools document**, with a loading time of approximately **180 ms**.

## 3xx / 4xx Responses

No significant 3xx or 4xx responses were observed in the main page requests. The successful requests returned **200 OK**.

## Summary

The W3Schools homepage generated approximately **43 network requests** after reloading the page with **Disable cache** enabled. The browser transferred approximately **1.8 MB** of data, while the total resource size was approximately **2.4 MB**.

The slowest observed resource was the main W3Schools document, which took approximately **180 ms**. The majority of the requests were successful and returned **200 OK** status codes.
