var chrtArea = document.getElementById("EnvironmentChart").getContext('2d');
var chrt = new Chart(chrtArea, {
    type: 'line',
    data: {},
    options: {
        scales: {
            xAxes: [{
                ticks: {
                    maxTicksLimit: 8
                }
            }],
            yAxes:[{
                id: "Temp",
                type: "linear",
                position: "left"
            }, {
                id: "Humi",
                type: "linear",
                position: "right"
            }]
        }
    }
});

function getEnvironmentData(range){
    var response = fetch("/data/environment/" + range[0] + "/" + range[1])
    var labels = [];
    response.labels.forEach(element => {
        labels.push(unixToHuman(element))
    });
    return {
        labels: labels,
        datasets: [{
            label: "Temperature",
            yAxisID: "Temp",
            data: response.temp
        },
        {
            label: "Humidity",
            yAxisID: "Humi",
            data: response.humi
        }]
    };
}


function unixToHuman(unix){
    var str = new Date(unix).toLocaleTimeString()
    return str
}
