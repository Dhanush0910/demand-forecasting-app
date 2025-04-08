let salesChart = null; // Global chart instance

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("predictBtn").addEventListener("click", getForecast);
    loadSalesData();
});

// Load actual sales data from the backend
async function loadSalesData() {
    try {
        let response = await fetch("/sales-data");
        let salesData = await response.json();

        console.log("Loaded Sales Data:", salesData);

        let dates = salesData.map(d => new Date(d.date).toISOString().split('T')[0]);
        let sales = salesData.map(d => Math.max(0, parseFloat(d.sales) || 0));

        console.log("Processed Actual Dates:", dates);
        console.log("Processed Actual Sales:", sales);

        // Store actual sales for reference
        sessionStorage.setItem("actualDates", JSON.stringify(dates));
        sessionStorage.setItem("actualSales", JSON.stringify(sales));

        drawChart(dates, sales, []);
    } catch (error) {
        console.error("Error fetching sales data:", error);
    }
}

// Fetch forecast data from the backend
async function getForecast() {
    let model = document.getElementById("modelSelect").value;
    let days = document.getElementById("daysInput").value;

    try {
        let response = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model: model, days: days })
        });

        let result = await response.json();
        console.log("API Response:", result);

        // format dates (assuming backend returns YYYY-MM-DD format)
        let forecastDates = result.dates.map(date => date.slice(0, 10));
        let forecastData = result.forecast.map(value => Math.max(0, parseFloat(value) || 0));

        let actualDates = JSON.parse(sessionStorage.getItem("actualDates")) || [];
        let actualSales = JSON.parse(sessionStorage.getItem("actualSales")) || [];

        // create a full sorted list of all unique dates
        let allDatesSet = new Set([...actualDates, ...forecastDates]);
        let allDates = Array.from(allDatesSet).sort((a, b) => new Date(a) - new Date(b));

        // map date → value
        let actualMap = Object.fromEntries(actualDates.map((d, i) => [d, actualSales[i]]));
        let forecastMap = Object.fromEntries(forecastDates.map((d, i) => [d, forecastData[i]]));

        let alignedActual = allDates.map(date => actualMap[date] ?? null);
        let alignedForecast = allDates.map(date => forecastMap[date] ?? null);

        console.log("Aligned Dates:", allDates);
        console.log("Aligned Actual:", alignedActual);
        console.log("Aligned Forecast:", alignedForecast);

        drawChart(allDates, alignedActual, alignedForecast);
    } catch (error) {
        console.error("Error fetching forecast data:", error);
    }
}


// Draw the chart with improved features
function drawChart(dates, sales, forecastData) {
    const canvas = document.getElementById('forecastChart');

    // ✅ set canvas height to ensure proper rendering
    canvas.height = 400;

    const ctx = canvas.getContext('2d');

    // destroy previous chart instance if it exists
    if (salesChart !== null) {
        salesChart.destroy();
    }

    salesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: "Actual Sales",
                    data: sales,
                    borderColor: "blue",
                    backgroundColor: "rgba(0, 0, 255, 0.2)",
                    fill: true,
                    pointRadius: 2,
                    pointHitRadius: 5,
                    lineTension: 0.4,
                    borderWidth: 2,
                },
                {
                    label: "Forecasted Sales",
                    data: forecastData,
                    borderColor: "red",
                    backgroundColor: "rgba(255, 0, 0, 0.2)",
                    fill: true,
                    pointRadius: 2,
                    pointHitRadius: 5,
                    lineTension: 0.4,
                    borderWidth: 2,
                    borderDash: [8, 4],
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'category',
                    title: {
                        display: true,
                        text: 'Date',
                        font: { size: 16 }
                    },
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: Math.min(20, dates.length / 2),
                        maxRotation: 45,
                        minRotation: 45,
                        font: { size: 12 }
                    },
                    grid: { display: false }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Sales',
                        font: { size: 16 }
                    },
                    beginAtZero: true,
                    suggestedMin: 0,
                    suggestedMax: Math.max(...sales, ...forecastData) * 1.2,
                    ticks: {
                        callback: value => value.toLocaleString(),
                        font: { size: 12 }
                    },
                    grid: { color: "rgba(0, 0, 0, 0.1)" }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        boxWidth: 20,
                        padding: 20,
                        font: { size: 14 }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: context => `${context.dataset.label}: ${context.raw?.toLocaleString() || 'N/A'}`
                    }
                },
                title: {
                    display: true,
                    text: 'Actual vs Forecasted Sales',
                    font: { size: 20 }
                },
                zoom: {
                    pan: {
                        enabled: true,
                        mode: 'x'
                    },
                    zoom: {
                        enabled: true,
                        mode: 'x'
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutCubic'
            },
            layout: {
                padding: {
                    left: 20,
                    right: 20,
                    top: 20,
                    bottom: 20,
                },
            },
        }
    });
}