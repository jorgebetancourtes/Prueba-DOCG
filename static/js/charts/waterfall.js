// funcion para traer datos de grafica de waterfall
function waterfall(nombre_grafica,dataXKey, dataYKey,dataZKey,path) {
    fetch(path)
    .then(response => {
        if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        const data_grafica = data;
        const x = data_grafica.map(item => item[dataXKey]);
        const y = data_grafica.map(item => item[dataYKey]);
        const z = data_grafica.map(item => item[dataZKey]);
        generar_grafica_waterfall(nombre_grafica, x, y,z);
    })
    .catch(error => {
        console.error("Error fetching or processing data:", error);
    });
};
// funcion praa generar grafica de waterfall
function generar_grafica_waterfall(selector, data_x, data_y,data_z, options = {}) {
    if (!selector || !document.querySelector(selector)) {
        console.error("Invalid selector or element not found:", selector);
        return;
    }

    let visibleBars = [];
    let hiddenBars = [];
    let categorias=[];
    let cumulativeTotal = 0;
    for (let i = 0; i < data_y.length; i++) {
        categoria=data_z[i];
        categorias.push(categoria);
        if(categoria==='Subtotal'){
            cumulativeTotal=0;
        }
        if (categoria!='Parcial'){
            hiddenBars.push(cumulativeTotal);
            visibleBars.push(data_y[i]); 
            cumulativeTotal += data_y[i]; // Update cumulative total
        }else{
            hiddenBars.push(cumulativeTotal-data_y[i]);
            visibleBars.push(data_y[i]); 
            cumulativeTotal -= data_y[i]; // Update cumulative total
        }
    }

    const defaultOptions = {
        tooltip: {
            enabledOnSeries: [1],
        },
        series: [
            {
                name: "Hidden Base",
                data: hiddenBars,
                color: "transparent",
                tooltip: {
                    enabled: false, // **Disable tooltip for hidden base**
                },
            },
            {
                name: "Importe",
                data: visibleBars,
                color: function ({ dataPointIndex }) {
                    if (categorias[dataPointIndex] !== 'Parcial') {
                        return "#267DFF"; 
                    }else{
                        return "#FF3232";
                    }
                },
            },
        ],
        legend: {
            show: false, // Hide series labels
        },
        chart: {
            height: 500,
            type: "bar",
            stacked: true, // Enables proper stacking for waterfall
            toolbar: { show: false },
            fontFamily: "Inter, sans-serif",
            tooltip: {
                enabled: true, // **Enable tooltips for visible bars**
            },
        },
        plotOptions: {
            bar: {
                columnWidth: "80%",
                borderRadius: 2,
                horizontal: false,
            },
        },
        dataLabels: {
            enabled: false, // **Disable data labels**
        },
        yaxis: {
            labels: {
                formatter: value => `$${value.toLocaleString()}`, // **Add $ to all numbers**
                style: { fontSize: "12px", fontWeight: "600", colors: "#7780A1" },

            },
        },
        xaxis: {
            categories: data_x,
            labels: {
                style: { fontSize: "12px", fontWeight: "600", colors: "#7780A1" },
            },
            axisBorder: {
                show: false, // **Hide the x-axis line**
            },
            axisTicks: {
                show: false, // **Hide the ticks**
            },
            lines: {
                show: false, // **Hide the gridlines separating the bars**
            },
        },
        grid: {
            borderColor: "#e0e6ed",
            strokeDashArray: 2,
        },
    };

    const mergedOptions = { ...defaultOptions, ...options };

    // Destroy existing chart if it exists
    const chartKey = selector.replace(/[^a-zA-Z0-9]/g, "");
    if (window[chartKey]) {
        window[chartKey].destroy();
    }

    // Create and render the new chart
    window[chartKey] = new ApexCharts(document.querySelector(selector), mergedOptions);
    window[chartKey].render();
}


