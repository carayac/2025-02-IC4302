var stats = {
    type: "GROUP",
name: "All Requests",
path: "",
pathFormatted: "group_missing-name--1146707516",
stats: {
    "name": "All Requests",
    "numberOfRequests": {
        "total": "505",
        "ok": "5",
        "ko": "500"
    },
    "minResponseTime": {
        "total": "62",
        "ok": "62",
        "ko": "1007"
    },
    "maxResponseTime": {
        "total": "35484",
        "ok": "80",
        "ko": "35484"
    },
    "meanResponseTime": {
        "total": "5051",
        "ok": "71",
        "ko": "5101"
    },
    "standardDeviation": {
        "total": "5537",
        "ok": "6",
        "ko": "5542"
    },
    "percentiles1": {
        "total": "1042",
        "ok": "70",
        "ko": "1043"
    },
    "percentiles2": {
        "total": "7152",
        "ok": "75",
        "ko": "7152"
    },
    "percentiles3": {
        "total": "19345",
        "ok": "79",
        "ko": "19346"
    },
    "percentiles4": {
        "total": "19534",
        "ok": "80",
        "ko": "19535"
    },
    "group1": {
    "name": "t < 800 ms",
    "htmlName": "t < 800 ms",
    "count": 5,
    "percentage": 1
},
    "group2": {
    "name": "800 ms <= t < 1200 ms",
    "htmlName": "t >= 800 ms <br> t < 1200 ms",
    "count": 0,
    "percentage": 0
},
    "group3": {
    "name": "t >= 1200 ms",
    "htmlName": "t >= 1200 ms",
    "count": 0,
    "percentage": 0
},
    "group4": {
    "name": "failed",
    "htmlName": "failed",
    "count": 500,
    "percentage": 99
},
    "meanNumberOfRequestsPerSecond": {
        "total": "0.559",
        "ok": "0.006",
        "ko": "0.554"
    }
},
contents: {
"req_health-endpoint--1499882823": {
        type: "REQUEST",
        name: "Health endpoint",
path: "Health endpoint",
pathFormatted: "req_health-endpoint--1499882823",
stats: {
    "name": "Health endpoint",
    "numberOfRequests": {
        "total": "5",
        "ok": "5",
        "ko": "0"
    },
    "minResponseTime": {
        "total": "62",
        "ok": "62",
        "ko": "-"
    },
    "maxResponseTime": {
        "total": "80",
        "ok": "80",
        "ko": "-"
    },
    "meanResponseTime": {
        "total": "71",
        "ok": "71",
        "ko": "-"
    },
    "standardDeviation": {
        "total": "6",
        "ok": "6",
        "ko": "-"
    },
    "percentiles1": {
        "total": "70",
        "ok": "70",
        "ko": "-"
    },
    "percentiles2": {
        "total": "75",
        "ok": "75",
        "ko": "-"
    },
    "percentiles3": {
        "total": "79",
        "ok": "79",
        "ko": "-"
    },
    "percentiles4": {
        "total": "80",
        "ok": "80",
        "ko": "-"
    },
    "group1": {
    "name": "t < 800 ms",
    "htmlName": "t < 800 ms",
    "count": 5,
    "percentage": 100
},
    "group2": {
    "name": "800 ms <= t < 1200 ms",
    "htmlName": "t >= 800 ms <br> t < 1200 ms",
    "count": 0,
    "percentage": 0
},
    "group3": {
    "name": "t >= 1200 ms",
    "htmlName": "t >= 1200 ms",
    "count": 0,
    "percentage": 0
},
    "group4": {
    "name": "failed",
    "htmlName": "failed",
    "count": 0,
    "percentage": 0
},
    "meanNumberOfRequestsPerSecond": {
        "total": "0.006",
        "ok": "0.006",
        "ko": "-"
    }
}
    },"req_animales-endpoi-2019602731": {
        type: "REQUEST",
        name: "Animales endpoint",
path: "Animales endpoint",
pathFormatted: "req_animales-endpoi-2019602731",
stats: {
    "name": "Animales endpoint",
    "numberOfRequests": {
        "total": "500",
        "ok": "0",
        "ko": "500"
    },
    "minResponseTime": {
        "total": "1007",
        "ok": "-",
        "ko": "1007"
    },
    "maxResponseTime": {
        "total": "35484",
        "ok": "-",
        "ko": "35484"
    },
    "meanResponseTime": {
        "total": "5101",
        "ok": "-",
        "ko": "5101"
    },
    "standardDeviation": {
        "total": "5542",
        "ok": "-",
        "ko": "5542"
    },
    "percentiles1": {
        "total": "1043",
        "ok": "-",
        "ko": "1043"
    },
    "percentiles2": {
        "total": "7152",
        "ok": "-",
        "ko": "7152"
    },
    "percentiles3": {
        "total": "19346",
        "ok": "-",
        "ko": "19346"
    },
    "percentiles4": {
        "total": "19535",
        "ok": "-",
        "ko": "19535"
    },
    "group1": {
    "name": "t < 800 ms",
    "htmlName": "t < 800 ms",
    "count": 0,
    "percentage": 0
},
    "group2": {
    "name": "800 ms <= t < 1200 ms",
    "htmlName": "t >= 800 ms <br> t < 1200 ms",
    "count": 0,
    "percentage": 0
},
    "group3": {
    "name": "t >= 1200 ms",
    "htmlName": "t >= 1200 ms",
    "count": 0,
    "percentage": 0
},
    "group4": {
    "name": "failed",
    "htmlName": "failed",
    "count": 500,
    "percentage": 100
},
    "meanNumberOfRequestsPerSecond": {
        "total": "0.554",
        "ok": "-",
        "ko": "0.554"
    }
}
    }
}

}

function fillStats(stat){
    $("#numberOfRequests").append(stat.numberOfRequests.total);
    $("#numberOfRequestsOK").append(stat.numberOfRequests.ok);
    $("#numberOfRequestsKO").append(stat.numberOfRequests.ko);

    $("#minResponseTime").append(stat.minResponseTime.total);
    $("#minResponseTimeOK").append(stat.minResponseTime.ok);
    $("#minResponseTimeKO").append(stat.minResponseTime.ko);

    $("#maxResponseTime").append(stat.maxResponseTime.total);
    $("#maxResponseTimeOK").append(stat.maxResponseTime.ok);
    $("#maxResponseTimeKO").append(stat.maxResponseTime.ko);

    $("#meanResponseTime").append(stat.meanResponseTime.total);
    $("#meanResponseTimeOK").append(stat.meanResponseTime.ok);
    $("#meanResponseTimeKO").append(stat.meanResponseTime.ko);

    $("#standardDeviation").append(stat.standardDeviation.total);
    $("#standardDeviationOK").append(stat.standardDeviation.ok);
    $("#standardDeviationKO").append(stat.standardDeviation.ko);

    $("#percentiles1").append(stat.percentiles1.total);
    $("#percentiles1OK").append(stat.percentiles1.ok);
    $("#percentiles1KO").append(stat.percentiles1.ko);

    $("#percentiles2").append(stat.percentiles2.total);
    $("#percentiles2OK").append(stat.percentiles2.ok);
    $("#percentiles2KO").append(stat.percentiles2.ko);

    $("#percentiles3").append(stat.percentiles3.total);
    $("#percentiles3OK").append(stat.percentiles3.ok);
    $("#percentiles3KO").append(stat.percentiles3.ko);

    $("#percentiles4").append(stat.percentiles4.total);
    $("#percentiles4OK").append(stat.percentiles4.ok);
    $("#percentiles4KO").append(stat.percentiles4.ko);

    $("#meanNumberOfRequestsPerSecond").append(stat.meanNumberOfRequestsPerSecond.total);
    $("#meanNumberOfRequestsPerSecondOK").append(stat.meanNumberOfRequestsPerSecond.ok);
    $("#meanNumberOfRequestsPerSecondKO").append(stat.meanNumberOfRequestsPerSecond.ko);
}
