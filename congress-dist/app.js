/* ===== 美国持仓监控 app.js ===== */
(function () {
  "use strict";

  var DATA = window.TRUMP_DATA || null;
  // 中英对照映射 (来自 trump_zh.js)
  var ZH = window.TRUMP_ZH || { ticker_zh: {}, name_zh: {} };
  var fmt = {
    // 中文单位美元: 18.1亿 / 5060万 / 12.3万
    money: function (n) {
      if (n == null || isNaN(n)) return "—";
      var v = Number(n), abs = Math.abs(v);
      if (abs >= 1e8) return (v / 1e8).toFixed(1) + "亿";
      if (abs >= 1e6) return (v / 1e4).toFixed(0) + "万";
      if (abs >= 1e4) return (v / 1e4).toFixed(1) + "万";
      if (abs >= 1e3) return (v / 1e3).toFixed(1) + "千";
      return v.toFixed(0);
    },
    pct: function (n) {
      if (n == null || isNaN(n)) return "—";
      return (n > 0 ? "+" : "") + n.toFixed(2) + "%";
    },
    // 金额区间字符串转中文单位: "$5,000,001 - $25,000,000" -> "$500万 - $2500万"
    range: function (s) {
      if (!s) return s;
      var m = String(s).match(/\$([\d,]+)\s*-\s*\$([\d,]+)/);
      if (!m) return s;
      var a = Number(m[1].replace(/,/g, "")), b = Number(m[2].replace(/,/g, ""));
      return "$" + this.money(a) + " - $" + this.money(b);
    },
  };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>\"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  // 取中文名：优先 ticker 映射，其次 name 全称映射，最后尝试 name 关键词
  function zhName(name, ticker) {
    if (ticker && ZH.ticker_zh[ticker]) return ZH.ticker_zh[ticker];
    if (name && ZH.name_zh[name]) return ZH.name_zh[name];
    if (name) {
      // 尝试长名字匹配 (name_zh 的 key 可能比当前 name 短/长)
      for (var k in ZH.name_zh) {
        if (name.indexOf(k) !== -1 || k.indexOf(name) !== -1) return ZH.name_zh[k];
      }
    }
    return "";
  }

  // 组装「英文(中文)」展示文本
  function nameWithZh(name, ticker) {
    var zh = zhName(name, ticker);
    if (!zh) return esc(name || "—");
    if (!name || name === ticker) return esc(zh);
    return esc(name) + '<span class="zh">' + esc(zh) + "</span>";
  }

  /* ---------- ECharts 实例 ---------- */
  var charts = {};

  /* ---------- 1. 渲染 Hero ---------- */
  function renderHero() {
    var s = DATA.summary;
    document.getElementById("updated") && (document.getElementById("updated").textContent = "");
    var sub = document.getElementById("heroSub");
    // heroSub 文案已移除（原「美国现任总统…披露」段落被删除）
    sub.innerHTML = "";
    var heroEl = document.getElementById("heroStats");
    var stats = [
      { v: s.total.toLocaleString(), l: "披露交易总数" },
      { v: s.stock.toLocaleString(), l: "股票交易" },
      { v: s.buy.toLocaleString(), l: "买入次数" },
      { v: s.sell.toLocaleString(), l: "卖出次数" },
      { v: fmt.money(s.est_volume), l: "估算交易额" },
    ];
    heroEl.innerHTML = stats.map(function (x) {
      return '<div class="hero-stat"><div class="val">' + esc(x.v) + '</div><div class="lbl">' + esc(x.l) + "</div></div>";
    }).join("");
  }

  /* ---------- 2. 持仓市值饼图 (2D) ---------- */
  function renderPie() {
    var el = document.getElementById("chartPie");
    var load = document.getElementById("chartPieLoading");
    load.style.display = "none";
    el.style.display = "block";

    var ch = echarts.init(el);
    charts["pie"] = ch;

    // 取前 12 大持仓，其余合并为「其他」
    var top = DATA.holdings.slice(0, 12);
    var rest = DATA.holdings.slice(12);
    var totalTop = top.reduce(function (a, h) { return a + (h.est_volume || 0); }, 0);
    var totalRest = rest.reduce(function (a, h) { return a + (h.est_volume || 0); }, 0);

    var data = top.map(function (h) {
      return {
        name: h.ticker,
        value: Math.round(h.est_volume),
        // 自定义字段供 tooltip/label 使用
        zh: zhName(h.name, h.ticker),
        fullname: h.name,
        buy: h.buy_count,
        sell: h.sell_count,
        ret: h.ret_30d_avg,
      };
    });
    if (totalRest > 0) {
      // 拆出「其他」切片的明细清单（按市值降序），供悬停 tooltip 展示
      var restItems = rest.slice().sort(function (a, b) {
        return (b.est_volume || 0) - (a.est_volume || 0);
      }).map(function (h) {
        return {
          ticker: h.ticker,
          zh: zhName(h.name, h.ticker),
          value: Math.round(h.est_volume || 0),
          pct: totalRest > 0 ? ((h.est_volume || 0) / totalRest * 100) : 0,
        };
      });
      data.push({
        name: "其他",
        value: Math.round(totalRest),
        zh: "其余持仓",
        fullname: "其余 " + rest.length + " 项持仓",
        buy: 0, sell: 0, ret: null,
        detail: restItems,
      });
    }

    // Apple 风格多色板
    var palette = ["#0071e3", "#5e5ce6", "#30b0c7", "#34c759", "#ff9f0a",
      "#ff375f", "#bf5af2", "#64d2ff", "#ac8e68", "#ffd60a",
      "#0a84ff", "#ff453a", "#a8a6ad"];

    var option = {
      color: palette,
      tooltip: {
        trigger: "item",
        formatter: function (p) {
          var d = p.data;
          var zh = d.zh ? "(" + d.zh + ")" : "";
          // 「其他」切片：显示含全部明细的可滚动列表
          if (d.detail) {
            var head = "<b>其他</b> " + esc(zh) + "<br/>" +
              "合计市值: <b>$" + fmt.money(d.value) + "</b> (占比 " + p.percent + "%)<br/>" +
              "共 " + d.detail.length + " 项持仓，明细如下：<br/>";
            var rows = d.detail.map(function (it) {
              return "<div class='tip-row'>" +
                "<span class='tip-tk'>" + esc(it.ticker) + "</span>" +
                (it.zh ? "<span class='tip-zh'>" + esc(it.zh) + "</span>" : "") +
                "<span class='tip-v'>$" + fmt.money(it.value) + "</span>" +
                "<span class='tip-p'>" + it.pct.toFixed(1) + "%</span>" +
                "</div>";
            }).join("");
            return head + "<div class='tip-list'>" + rows + "</div>";
          }
          var lines = "<b>" + esc(d.name) + "</b> " + esc(zh) + "<br/>" +
            "市值: <b>$" + fmt.money(d.value) + "</b> (" + p.percent + "%)";
          if (d.fullname && d.fullname !== d.name) lines += "<br/>" + esc(d.fullname);
          if (d.ret != null) lines += "<br/>30日收益: " + fmt.pct(d.ret);
          return lines;
        },
      },
      series: [{
        type: "pie",
        radius: ["40%", "68%"],
        center: ["50%", "48%"],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 8, borderColor: "#fff", borderWidth: 2 },
        label: {
          show: true,
          formatter: function (p) {
            var d = p.data;
            var zh = d.zh ? " " + d.zh : "";
            return d.name + zh + "\n" + p.percent.toFixed(1) + "%";
          },
          color: "#1d1d1f", fontSize: 11,
        },
        labelLine: { length: 14, length2: 10, lineStyle: { color: "#d2d2d7" } },
        emphasis: {
          label: { show: true, fontWeight: 700 },
          itemStyle: { shadowBlur: 16, shadowColor: "rgba(0,0,0,0.15)" },
        },
        data: data,
      }],
    };

    ch.setOption(option);
    if (window.addEventListener) {
      window.addEventListener("resize", function () { ch.resize(); });
    }
  }

  /* ---------- 3. KPI 卡片 ---------- */
  function renderKPI() {
    var s = DATA.summary;
    var grid = document.getElementById("kpiGrid");
    var items = [
      { l: "逾期披露率", v: s.late_rate + "%", f: "超过45天STOCK Act期限", small: true },
      { l: "中位披露延迟", v: s.median_delay + " 天", f: "交易到披露的中位天数", small: true },
      { l: "个股持仓数", v: DATA.holdings.length, f: "带股票代码的持仓", small: true },
      { l: "最大持仓", v: DATA.holdings[0] ? DATA.holdings[0].ticker : "—", f: DATA.holdings[0] ? fmt.money(DATA.holdings[0].est_volume) + " 估算市值" : "", small: true },
    ];
    grid.innerHTML = items.map(function (x) {
      return '<div class="kpi"><div class="k-label">' + esc(x.l) + '</div>' +
        '<div class="k-val small">' + esc(x.v) + '</div>' +
        '<div class="k-foot">' + esc(x.f) + "</div></div>";
    }).join("");
  }

  /* ---------- 4. 时间趋势折线 ---------- */
  function renderTimeline() {
    var el = document.getElementById("chartTimeline");
    var ch = echarts.init(el);
    charts["tl"] = ch;
    var months = DATA.timeline.map(function (t) { return t.month; });
    var buy = DATA.timeline.map(function (t) { return Math.round(t.buy); });
    var sell = DATA.timeline.map(function (t) { return Math.round(t.sell); });
    ch.setOption({
      tooltip: { trigger: "axis", valueFormatter: function (v) { return "$" + fmt.money(v); } },
      legend: { data: ["买入", "卖出"], top: 6, icon: "roundRect", itemWidth: 14, itemHeight: 8 },
      grid: { left: 12, right: 16, top: 48, bottom: 20, containLabel: true },
      xAxis: {
        type: "category", data: months, boundaryGap: false,
        axisLabel: { color: "#86868b", fontSize: 11, rotate: 0 },
        axisLine: { lineStyle: { color: "#e8e8ed" } },
        axisTick: { show: false },
      },
      yAxis: {
        type: "value",
        axisLabel: { color: "#86868b", fontSize: 11, formatter: function (v) { return fmt.money(v); } },
        splitLine: { lineStyle: { color: "#f0f0f3" } },
      },
      series: [
        {
          name: "买入", type: "line", smooth: true, data: buy,
          symbol: "circle", symbolSize: 6,
          lineStyle: { width: 3, color: "#34c759" },
          itemStyle: { color: "#34c759" },
          areaStyle: { color: "rgba(52,199,89,0.10)" },
        },
        {
          name: "卖出", type: "line", smooth: true, data: sell,
          symbol: "circle", symbolSize: 6,
          lineStyle: { width: 3, color: "#ff3b30" },
          itemStyle: { color: "#ff3b30" },
          areaStyle: { color: "rgba(255,59,48,0.08)" },
        },
      ],
    });
    window.addEventListener("resize", function () { ch.resize(); });
  }

  /* ---------- 5. 持仓排行榜 ---------- */
  function renderHoldings() {
    var list = document.getElementById("holdingsList");
    document.getElementById("holdingsCount").textContent = "共 " + DATA.holdings.length + " 个持仓";
    if (!DATA.holdings.length) {
      list.innerHTML = '<div style="padding:24px;color:var(--text-tertiary);text-align:center;">暂无持仓数据</div>';
      return;
    }
    var headHtml =
      '<div class="holding-row hold-head">' +
        '<div class="rank">#</div>' +
        '<div class="tick-wrap"><span class="thead">代码</span></div>' +
        '<div class="name-wrap"><span class="thead">公司名称</span></div>' +
        '<div class="bs"><span class="thead">买卖次数</span></div>' +
        '<div class="vol"><span class="thead">市值</span></div>' +
        '<span class="ret-chip thead-chip">涨跌幅</span>' +
      "</div>";
    list.innerHTML = headHtml + DATA.holdings.slice(0, 24).map(function (h, i) {
      var ret = h.ret_30d_avg;
      // 无涨跌幅时用占位符"–"占位，保证 ret-chip 列存在、布局对齐
      var retChip = ret == null ? '<span class="ret-chip na">–</span>' :
        '<span class="ret-chip ' + (ret >= 0 ? "up" : "down") + '">' + fmt.pct(ret) + "</span>";
      // 中英: 中文名放 ticker badge 下方
      var zh = zhName(h.name, h.ticker);
      var tickerBadge = '<div class="ticker-badge">' + esc(h.ticker) + "</div>";
      var zhSub = zh ? '<div class="ticker-zh">' + esc(zh) + "</div>" : "";
      return '<div class="holding-row">' +
        '<div class="rank">' + (i + 1) + "</div>" +
        '<div class="tick-wrap">' + tickerBadge + zhSub + "</div>" +
        '<div class="name-wrap">' +
          '<div class="name">' + esc(h.name) + "</div>" +
        "</div>" +
        '<div class="bs">' +
          '<span class="chip buy" title="买入次数">买' + h.buy_count + "</span>" +
          '<span class="chip sell" title="卖出次数">卖' + h.sell_count + "</span>" +
        "</div>" +
        '<div class="vol"><span class="unit">$</span>' + fmt.money(h.est_volume) + "</div>" +
        retChip +
      "</div>";
    }).join("");
  }

  /* ---------- 6. 重大交易表格 ---------- */
  function renderTrades() {
    var tbody = document.querySelector("#tradesTable tbody");
    var rows = DATA.topTrades || [];
    tbody.innerHTML = rows.map(function (t) {
      var ret = t.ret_30d;
      var retChip = ret == null ? '<span style="color:var(--text-tertiary)">—</span>' :
        '<span class="ret-chip ' + (ret >= 0 ? "up" : "down") + '">' + fmt.pct(ret) + "</span>";
      var tk = t.ticker ? '<span class="tk">' + esc(t.ticker) + "</span>" : '<span style="color:var(--text-tertiary)">—</span>';
      var latetag = t.is_late ? '<span class="latetag">逾期</span>' : "";
      // 资产名中英标注
      var zh = zhName(t.name, t.ticker);
      var nameHtml = esc(t.name) + (zh ? '<span class="zh">' + esc(zh) + "</span>" : "");
      return "<tr>" +
        "<td>" + esc(t.date) + "</td>" +
        "<td>" + nameHtml + "</td>" +
        "<td>" + tk + "</td>" +
        "<td>" + (t.type === "买入" ? '<span class="chip buy">买入</span>' : '<span class="chip sell">卖出</span>') + "</td>" +
        "<td>" + esc(fmt.range(t.amount)) + "</td>" +
        "<td>" + retChip + "</td>" +
        "<td>" + latetag + "</td>" +
      "</tr>";
    }).join("");
  }

  /* ---------- 启动 ---------- */
  function init() {
    if (!DATA) {
      document.getElementById("heroSub").textContent = "数据加载失败，请稍后重试。";
      document.getElementById("chartPieLoading").innerHTML = "数据加载失败";
      return;
    }
    renderHero();
    renderKPI();
    renderHoldings();
    renderTrades();
    // 时间显示
    var up = document.getElementById("updateTime");
    if (up) up.textContent = "数据更新于 " + (DATA.meta.updated || "");
    // 饼图与折线图稍后渲染，避免阻塞首屏
    setTimeout(renderPie, 30);
    setTimeout(renderTimeline, 40);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
