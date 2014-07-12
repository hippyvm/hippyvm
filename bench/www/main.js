d3.json('data.json', function(data) {

	nv.addGraph(function() {
		var chart = nv.models.multiBarChart()
			.x(function(d) { return d.label })
			.y(function(d) { return d.value })
			.margin({top: 30, right: 20, bottom: 50, left: 100})
			.tooltips(true)
			.showControls(false);

		chart.yAxis.tickFormat(d3.format(',.2f'));

		d3.select('#chart1 svg').datum(data).call(chart);

		return chart;
	});

});
