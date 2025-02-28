// returns an array of [ticker_text, config]
function ticker_data (ticker_text) {

    const Date = [];
    const Yield_Spread = [];
    const Price = [];

    console.log ("about to grab the data");
    d3.csv(`../static/${ticker_text}_yield_curve.csv`) // Grab csv
    .then(function(data) { 
        // console.log(data);
        // Date column is just a string. Test if it's type needs to be changed.
        // console.log(typeof data[5000]["Date"]);
        
        // Place columns into arrays
        for (i = 0; i < data.length; i++){
            Date.push(data[i]["Date"]);
            Yield_Spread.push(+data[i]["spread_10_3"]);
            Price.push(+data[i]["Adj Close"]);
        }
        console.log("finished getting the data");
    });

    const config = {
        type: "line",
        data: {
            labels: Date,
            datasets: [
                {
                    label: "Price",
                    yAxisID: "y",
                    data: Price,
                    borderColor: "#33FF3F",
                    pointStyle: false
                },
                {
                    label: "Yield Spread",
                    yAxisID: "y1",
                    data: Yield_Spread,
                    borderColor: "#3349FF",
                    pointStyle: false
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            stacked: false,
            plugins: {
                title: {
                display: true,
                text: `${ticker_text} Prices vs. Yield Spread`
                }
            },
            scales: {
                y: {
                type: 'linear',
                display: true,
                position: 'left',
                },
                y1: {
                type: 'linear',
                display: true,
                position: 'right',
        
                // grid line settings
                grid: {
                    drawOnChartArea: false, // only want the grid lines for one axis to show up
                },
                },
            },
        }
    };

    return [ticker_text, config];
};

// console.log(ticker_data("IYW"));
var init_data = ticker_data("IYW");
var canvas = document.getElementById("line_chart");

// console.log(init_data[1]);
// console.log(new Chart(canvas, init_data[1]));
// BUG: INITAL CHART DOESNT RENDER UNLESS I OPEN CONSOLE
let my_line_chart = new Chart(canvas, init_data[1]);


function chart_destroy() {
    my_line_chart.destroy();
};

function chart_render() {
    var input_text = document.getElementById("ticker_text").value;
    var new_config = ticker_data(input_text)[1];
    my_line_chart = new Chart(canvas, new_config);
    // my_line_chart.update();
    // my_line_chart.update();
};

