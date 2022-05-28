$(window).load( function() {
    $.getJSON( "music_info.json", function(obj) {
        $.each(obj, function(key, value) {

            let encodeID = value.encodeId;
            let stream = value.streams;
            for (const item in stream) {
                let tmp = Object.keys(stream[item]);
                if (stream[item][tmp] != "VIP") {
                    let str = '<p style="color:red;font-size:20px">';
                    str += key + ' .-. <a href="/song_info.html?id=' + encodeID + '">';
                    str += value.title + ' ' + tmp + 'kb</a>';
                    str += '</p>';
                    $("ul").append(str);
                };
            };

        });
    });
});