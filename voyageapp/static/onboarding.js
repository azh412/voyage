document.addEventListener('DOMContentLoaded', function() {
    console.log("Hello, world")
    var x = []
    // document.querySelector('#next_topic').addEventListener('click', add_interest);
    // document.querySelector('#sub2').addEventListener('click', step2transition);
    function add_interest() {
        var topic = document.getElementById("topic").value
        if(topic == null || topic.length == 0){
            return
        }
        if(topic != '') {
            x.push(topic)
            if(x.length >= 8){
                document.getElementById("info1").innerHTML = "Alright, that should be enough for us to know what you're into. Feel free to add more to improve the process. When you're done, press 'I'm done'."
            }
            else{
                console.log()
                document.getElementById("info1").innerHTML = "Great! Give me " + (8 - x.length.toString()) + "more!"
            }
        }
        console.log(x)
        document.getElementById("topic").value = ""
    }
    function hello(){
        alert("hello");
    }
    function step2transition(){
        alert(x[0])
        console.log(x[0])
    }
  });

  