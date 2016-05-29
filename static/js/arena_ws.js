try{
    var sock = new WebSocket('ws://' + window.location.host + '/arena/ws');
}
catch(err){
    var sock = new WebSocket('wss://' + window.location.host + '/arena/ws');
}

// show message in div#subscribe
function showMessage(message) {}

sock.onopen = function(){
    showMessage('Connection to server started')
}

function normalize_coords(coords){
    var div = $('.arena_field');
    var h = div.height();
    var w = div.width();
    return {
        'x': coords.x * w / 1000,
        'y': coords.y * h / 1000
    }
}

function update_ally(parsed_data)
{
    var account_id = parsed_data.account_id;
    $('.teammate').not("#myVehicle").remove();
    for (key in parsed_data.vehicles) {
        if (parsed_data.vehicles.hasOwnProperty(key)){
            var vehicle_info = parsed_data.vehicles[key];

            tank = $('.' + vehicle_info.id).find('svg').clone();
            tank.addClass("teammate");
            $('.arena_field').append(tank);
            var pos = normalize_coords(vehicle_info);
            tank[0].setAttribute('y',  pos.y - vehicle_info.height / 2);
            tank[0].setAttribute('x',  pos.x - vehicle_info.width / 2);

            if (key != account_id){
                tank.css(
                    { opacity: 0.4, filter: "alpha(opacity=40)" /* For IE8 and earlier */ });
            }
        }
    }
}

function createBaseLine(div, x1,y1, x2,y2){
    var obj = document.createElementNS("http://www.w3.org/2000/svg", "line");
    obj.setAttributeNS(null, "class", "line");
    obj.setAttributeNS(null, "x1", x1);
    obj.setAttributeNS(null, "y1", y1);
    obj.setAttributeNS(null, "x2", x2);
    obj.setAttributeNS(null, "y2", y2);
    obj.setAttributeNS(null, "stroke", "black");
    obj.setAttributeNS(null, "stroke-width", 2);
    div[0].appendChild(obj);
}

function createLine(div, offset) {
    var h = div.height();
    var w = div.width();
    return createBaseLine(div, w/2 + offset, 0, w/2 - offset, h);
}

function create_shot(arena_field, base_shot, x, y, alpha){
    shot = base_shot.clone();
    shot.addClass('shot');
    arena_field.append(shot);
    shot[0].setAttribute('y', y);
    shot[0].setAttribute('x', x);
    shot.css(
        { opacity: alpha/100, filter: "alpha(opacity=" + alpha + ")" /* For IE8 and earlier */ });

}

function sync_arena(parsed_data){
    $('.teammate,.enemy').remove();
    $('.shot').remove();
    $('.line').remove();
    var arena_feld = $('.arena_field')

    for (key in parsed_data.ally) {
        if (parsed_data.ally.hasOwnProperty(key)){
            var vehicle_info = parsed_data.ally[key];
            tank = $('.' + vehicle_info.id).find('svg').clone();
            tank.addClass("teammate");
            arena_feld.append(tank);
            var pos = normalize_coords(parsed_data.ally[key]);
            tank[0].setAttribute('y',  pos.y - vehicle_info.height / 2);
            tank[0].setAttribute('x',  pos.x - vehicle_info.width / 2);
        }
    }
    for (key in parsed_data.enemy) {
        if (parsed_data.enemy.hasOwnProperty(key)){
            var vehicle_info = parsed_data.enemy[key];
            tank = $('.' + vehicle_info.id).find('svg').clone();
            tank.addClass("enemy");
            arena_feld.append(tank);
            var pos = normalize_coords(parsed_data.enemy[key]);
            tank[0].setAttribute('y',  pos.y - vehicle_info.height / 2);
            tank[0].setAttribute('x',  arena_feld.width() - pos.x - vehicle_info.width / 2);
        }
    }

    var base_shot = $('.shot-template svg');
    $.map(parsed_data.shots.enemy, function(data){
        var pos = normalize_coords(data.position);
        create_shot(
            arena_feld,
            base_shot,
            pos.x - vehicle_info.width / 2,
            pos.y - vehicle_info.height / 2,
            data.alpha);
    });

    $.map(parsed_data.shots.ally, function(data){
        var pos = normalize_coords(data.position);
        create_shot(
            arena_feld, base_shot,
            arena_feld.width() - pos.x - vehicle_info.width / 2,
            pos.y - vehicle_info.height / 2,
            data.alpha)
    });

    createLine($('.arena_field'), parsed_data.divider);
}

function update_countdown(parsed_data){
    var countdown_div =$('.arena_field').find('.countdown');
    if (!countdown_div.length){
        var countdown_div = $('<div class="countdown"></div>');
        countdown_div.css({'text-align': 'center'});
        $('.arena_field').prepend(countdown_div);
    }
    countdown_div.html(parsed_data.left);
}

function update_shot(parsed_data){
    var aim =$('.arena_field').find('.aim');
    if (!aim.length){
        aim = $('.aim-template svg').clone();
        aim.addClass('aim');
        $('.arena_field').append(aim);
    }
    var pos = normalize_coords(parsed_data.data);
    aim[0].setAttribute('y',  pos.y - 32);
    aim[0].setAttribute('x',  pos.x - 32);
}

// income message handler
sock.onmessage = function(event) {
  var parsed_data = JSON.parse(event.data);
  if (parsed_data.command == 'update_vehicles'){
    update_ally(parsed_data);
  }
  if (parsed_data.command == 'sync_arena'){
    sync_arena(parsed_data);
  }
  if (parsed_data.command == 'update_countdown'){
    update_countdown(parsed_data);
  }
  if (parsed_data.command == 'update_shot'){
    update_shot(parsed_data);
  }
//   showMessage(event.data);
};

$(function(){
    $('.arena_field').click(function(event){
        sock.send(
            JSON.stringify(
                {
                    "y": event.offsetY,
                    "x": event.offsetX,
                    "height": $(this).height(),
                    "width": $(this).width()
                }
            )
        );
    });
})

$('#signout').click(function(){
    window.location.href = "signout"
});

sock.onclose = function(event){
    if(event.wasClean){
        showMessage('Clean connection end')
    }else{
        showMessage('Connection broken')
    }
};

sock.onerror = function(error){
    showMessage(error);
}
