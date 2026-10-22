(function(){
  const store = {
    get(k, d){ try{ const v = localStorage.getItem("sp:"+k); return v===null ? d : JSON.parse(v); }catch(e){ return d; } },
    set(k, v){ try{ localStorage.setItem("sp:"+k, JSON.stringify(v)); }catch(e){} }
  };
  window.SP = { store };

  // light/dark switch
  const t = store.get("theme", null);
  if (t) document.documentElement.dataset.theme = t;
  SP.toggleTheme = function(btn){
    const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = next; store.set("theme", next);
    if (btn) btn.textContent = next === "light" ? "Dark" : "Light";
  };

  // dates are relative to today so the demo never goes stale
  const DAY = 864e5;
  const today = new Date(); today.setHours(0,0,0,0);
  SP.today = today;
  SP.dayDate = i => new Date(today.getTime() + i*DAY);
  SP.examDate = () => SP.dayDate(COURSE.examInDays);
  SP.fmt = d => d.toLocaleDateString("en-GB", { weekday:"short", day:"numeric", month:"short" });

  // shared top bar
  SP.bar = function(current){
    const pages = [["syllabus.html","1 · Syllabus"],["revision.html","2 · Revision"],["plan.html","3 · Study Plan"]];
    const el = document.getElementById("bar");
    el.innerHTML = '<a class="brand" href="index.html"><i></i>' + COURSE.name + '</a><nav class="tabs" aria-label="Study pack">' +
      pages.map(p => '<a href="'+p[0]+'"'+(p[0]===current?' aria-current="page"':'')+'>'+p[1]+'</a>').join("") +
      '</nav><span class="sp"></span><span class="chip">Exam ' + SP.fmt(SP.examDate()) + '</span>' +
      '<button class="btn" type="button" id="themeBtn">' + (document.documentElement.dataset.theme==="light"?"Dark":"Light") + '</button>';
    document.getElementById("themeBtn").addEventListener("click", e => SP.toggleTheme(e.currentTarget));
  };

  // MathJax
  window.MathJax = { tex:{ inlineMath:[["\\(","\\)"]], displayMath:[["\\[","\\]"]] }, svg:{ fontCache:"global" },
    startup:{ ready(){ MathJax.startup.defaultReady(); MathJax.startup.promise.then(() => { document.documentElement.classList.add("mj-ready"); }); } } };
})();
