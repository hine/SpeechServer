(function() {

  var hostname = location.host;
  var ws = new WebSocket("ws://" + hostname + "/ws");

  ws.onopen = function() {
    // WebSocketオープン時の挙動を書く
    ws.send(JSON.stringify({command: "voice_list"}));
  };

  ws.onmessage = function (evt) {
    // WebSocketでメッセージを受け取った時の処理をまとめて
    try {
      console.log(evt.data)
      var messageData = JSON.parse(evt.data);
      parseMessage(messageData);
    } catch(e) {
      alert('受け取ったメッセージの形式が不正です [response]:' + messageData['response']);
    }
  };

  $('#send-text').on('click', function() {
    if ($('#voice').val() == '') {
      alert("ボイスファイルを指定してください。");
    } else {
      ws.send(JSON.stringify({command: "say", data: {text: $('#speech-text').val(), voice: $('#voice').val()}}));
    }
  });

  $('#speech-text').on('change keyup', function() {
    buttonEnable($('#send-text'));
  });

  function parseMessage(messageData) {
    // WebSocketで受け取ったJSONメッセージの処理
    console.log(messageData);
    response = messageData['response']
    if (response == 'voice_list') {
      console.log(messageData['data']);
    }
  }

  function buttonEnable(button) {
    button.prop("disabled", false);
    button.prop("className", "button");
  }

  function buttonDisable(button) {
    button.prop("disabled", true);
    button.prop("className", "button-disable");
  }

  function printJSON() {
    $('#json-data').val(JSON.stringify(json, null, '  '));
  }

  function updateJSON(data) {
      json = data;
      printJSON();
  }

  function showPath(path) {
    $('#path').text(path);
  }

})();
