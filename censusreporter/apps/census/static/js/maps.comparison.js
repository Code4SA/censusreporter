// Given a set of geographies and a dataset,
// draws a D3 choropleth map

// the template including this should set the following vars:
// var geodata = {{ map_data }},
//     tabledata = {{ table_data }},
//     percentify = '{{ percentify }}',
//     parent_fips_code = '{{ parent_fips_code }}';
// 
// var parent = {{ parent_shape }},
//     children = {{ child_shapes }};


var mapDiv = d3.select("#data-map")
    .attr("class", "svg-map");

var width = mapDiv[0][0].offsetWidth;
var height = width*.67;

mapDiv.style("height", height);

var svgMap = mapDiv.append("svg")
    .attr("width", width)
    .attr("height", height)
    .style("float", "left")
    .style("position", "relative");

var label = mapDiv.append("div")
    .attr("class", "label")
    .style("opacity", 1e-6);

var labelTitle = "";

var columns = d3.entries(tabledata['columns']);

// add dropdown
d3.select("#map-select").append("select")
    .attr("id", "map-select-select")
    .on("change", changeMap)
.selectAll("option").data(columns).enter().append("option")
    .attr("value", function(d){ return d['key']; })
    .attr("disabled", function(d){ return (d['key'].indexOf('.') >= 0) ? true : null; })
    .text(function(d){
            var indents = new Array(d['value']['indent']);
            return indents.join("\xA0\xA0") + d['value']['name'];
        })

// make the map, defaulting to first column of data
makeMap(geodata[columns[0]['key']]);
window.labelTitle = columns[0]['value']['full_name'];

// rebuild map with new data on select menu change
function changeMap() {
    var dataIndex = this.options[this.selectedIndex].value;
    window.labelTitle = tabledata['columns'][dataIndex]['full_name'];
    makeMap(geodata[dataIndex]);
}

function makeMap(geodata) {
    if (!!percentify) {
        var values = d3.values(geodata).map(function(d) {return d['percentage'];});
    } else {
        var values = d3.values(geodata).map(function(d) {return d['value'];});
    }
    var quantize = d3.scale.quantile()
        .domain([d3.min(values), d3.max(values)])
        .range(d3.range(5).map(function(i) { return "q" + i; }));

    var labelData = quantize.quantiles().slice(0);
    labelData.unshift(d3.min(values));
    labelData.push(d3.max(values));
    var legendLabels = d3.select("#map-legend")
        .selectAll("span")
        .data(labelData)
        .text(function(d){
            if (typeof(d) != 'undefined') {
                if (!!percentify) {
                    return roundNumber(d) + '%'
                } else {
                    return numberWithCommas(d)
                }
            }
        });
        
    // zoom to the parent
    var projection = d3.geo.albersUsa().precision(.3);

    if (!!parent_fips_code && parent_fips_code != '02' && parent_fips_code != '15') {
        projection = d3.geo.mercator().precision(1000);
    }

    var path = d3.geo.path()
        .projection(projection);

    if (!!parent) {
        // zoom to bounding box of parent
        projection
            .scale(1)
            .translate([0, 0]);

        var b = path.bounds(parent),
            s = .95 / Math.max((b[1][0] - b[0][0]) / width, (b[1][1] - b[0][1]) / height),
            t = [(width - s * (b[1][0] + b[0][0])) / 2, (height - s * (b[1][1] + b[0][1])) / 2];

        projection
            .scale(s)
            .translate(t);
    } else {
        // standard projection to show whole U.S.
        projection
            .scale(1000)
            .translate([width / 2, height / 2]);
    }

    // outline the parent geography
    svgMap.append("path")
        .datum(parent)
        .attr("d", path)
        .attr("class", "outline");

    // add the quantiled child geographies
    svgMap.append("g")
            .attr("class", "geographies")
        .selectAll("path")
            .data(children)
        .enter().append("path")
            .attr("d", path)
            .attr("id", function(d) { return "poly-" + d['id']; })
            .attr("class", function(d) {
                if (!!geodata[d['id']]) {
                    if (!!percentify) {
                        return quantize(geodata[d['id']]['percentage']);
                    } else {
                        return quantize(geodata[d['id']]['value']);
                    }
                }
            })
            .on("mouseover", function(d) { return mouseover(d) })
            .on("mousemove", mousemove)
            .on("mouseout", mouseout);

    function mouseover(d) {
        if (!!geodata[d['id']]) {
            var centroid = path.centroid(d),
                x = centroid[0],
                y = centroid[1];

            label
                .html(makeLabel(d))
                .transition()
                .duration(200)
                .style("width", "200px")
                .style("opacity", 1);
                //.style("left", x + "px")
                //.style("top", y + "px");
        }
    }

    function mousemove() {
        label
            .style("left", (d3.mouse(this)[0] - 100) + "px")
            .style("bottom", height-(d3.mouse(this)[1] - 12) + "px");
    }

    function mouseout() {
        label.transition()
            .duration(200)
            .style("opacity", 1e-6);
    }

    function makeLabel(d) {
        if (!!geodata[d['id']]) {
            var label = "<span class='label-title'>" + labelTitle + "</span>";
            label += "<span class='name'>" + geodata[d['id']]['name'] + "</span>";
            if (!!geodata[d['id']]['percentage']) {
                label += "<span class='value'>" + geodata[d['id']]['percentage'] + "%";
                if (!!geodata[d['id']]['value']) {
                    label += " (" + numberWithCommas(geodata[d['id']]['value']) + ")";
                }
                label += "</span>";
            }
            else if (!!geodata[d['id']]['value']) {
                label += "<span class='value'>" + numberWithCommas(geodata[d['id']]['value']) + "</span>";
            }
        }
        return label
    }
    //svg.selectAll(".label")
        //    .data(geographies.features)
        //.enter().append("text")
        //    .attr("id", function(d) { return "label-" + d['id']; })
        //    .attr("class", "label")
        //    .attr("transform", function(d) { return "translate(" + path.centroid(d) + ")"; })
        //    .text(function(d) { return d['properties']['name'] + geodata[d['id']]; });
}