"use strict";
(self.webpackChunkwormspy = self.webpackChunkwormspy || []).push([
  [179],
  {
    233: () => {
      function ae(n) {
        return "function" == typeof n;
      }
      function Cs(n) {
        const t = n((i) => {
          Error.call(i), (i.stack = new Error().stack);
        });
        return (
          (t.prototype = Object.create(Error.prototype)),
          (t.prototype.constructor = t),
          t
        );
      }
      const Xo = Cs(
        (n) =>
          function (t) {
            n(this),
              (this.message = t
                ? `${t.length} errors occurred during unsubscription:\n${t
                    .map((i, r) => `${r + 1}) ${i.toString()}`)
                    .join("\n  ")}`
                : ""),
              (this.name = "UnsubscriptionError"),
              (this.errors = t);
          }
      );
      function ar(n, e) {
        if (n) {
          const t = n.indexOf(e);
          0 <= t && n.splice(t, 1);
        }
      }
      class Le {
        constructor(e) {
          (this.initialTeardown = e),
            (this.closed = !1),
            (this._parentage = null),
            (this._teardowns = null);
        }
        unsubscribe() {
          let e;
          if (!this.closed) {
            this.closed = !0;
            const { _parentage: t } = this;
            if (t)
              if (((this._parentage = null), Array.isArray(t)))
                for (const s of t) s.remove(this);
              else t.remove(this);
            const { initialTeardown: i } = this;
            if (ae(i))
              try {
                i();
              } catch (s) {
                e = s instanceof Xo ? s.errors : [s];
              }
            const { _teardowns: r } = this;
            if (r) {
              this._teardowns = null;
              for (const s of r)
                try {
                  kp(s);
                } catch (o) {
                  (e = null != e ? e : []),
                    o instanceof Xo ? (e = [...e, ...o.errors]) : e.push(o);
                }
            }
            if (e) throw new Xo(e);
          }
        }
        add(e) {
          var t;
          if (e && e !== this)
            if (this.closed) kp(e);
            else {
              if (e instanceof Le) {
                if (e.closed || e._hasParent(this)) return;
                e._addParent(this);
              }
              (this._teardowns =
                null !== (t = this._teardowns) && void 0 !== t ? t : []).push(
                e
              );
            }
        }
        _hasParent(e) {
          const { _parentage: t } = this;
          return t === e || (Array.isArray(t) && t.includes(e));
        }
        _addParent(e) {
          const { _parentage: t } = this;
          this._parentage = Array.isArray(t) ? (t.push(e), t) : t ? [t, e] : e;
        }
        _removeParent(e) {
          const { _parentage: t } = this;
          t === e ? (this._parentage = null) : Array.isArray(t) && ar(t, e);
        }
        remove(e) {
          const { _teardowns: t } = this;
          t && ar(t, e), e instanceof Le && e._removeParent(this);
        }
      }
      Le.EMPTY = (() => {
        const n = new Le();
        return (n.closed = !0), n;
      })();
      const Ip = Le.EMPTY;
      function xp(n) {
        return (
          n instanceof Le ||
          (n && "closed" in n && ae(n.remove) && ae(n.add) && ae(n.unsubscribe))
        );
      }
      function kp(n) {
        ae(n) ? n() : n.unsubscribe();
      }
      const xi = {
          onUnhandledError: null,
          onStoppedNotification: null,
          Promise: void 0,
          useDeprecatedSynchronousErrorHandling: !1,
          useDeprecatedNextContext: !1,
        },
        Jo = {
          setTimeout(...n) {
            const { delegate: e } = Jo;
            return ((null == e ? void 0 : e.setTimeout) || setTimeout)(...n);
          },
          clearTimeout(n) {
            const { delegate: e } = Jo;
            return ((null == e ? void 0 : e.clearTimeout) || clearTimeout)(n);
          },
          delegate: void 0,
        };
      function Fp(n) {
        Jo.setTimeout(() => {
          const { onUnhandledError: e } = xi;
          if (!e) throw n;
          e(n);
        });
      }
      function ws() {}
      const ZM = Ic("C", void 0, void 0);
      function Ic(n, e, t) {
        return { kind: n, value: e, error: t };
      }
      let ki = null;
      function ea(n) {
        if (xi.useDeprecatedSynchronousErrorHandling) {
          const e = !ki;
          if ((e && (ki = { errorThrown: !1, error: null }), n(), e)) {
            const { errorThrown: t, error: i } = ki;
            if (((ki = null), t)) throw i;
          }
        } else n();
      }
      class xc extends Le {
        constructor(e) {
          super(),
            (this.isStopped = !1),
            e
              ? ((this.destination = e), xp(e) && e.add(this))
              : (this.destination = e0);
        }
        static create(e, t, i) {
          return new kc(e, t, i);
        }
        next(e) {
          this.isStopped
            ? Rc(
                (function XM(n) {
                  return Ic("N", n, void 0);
                })(e),
                this
              )
            : this._next(e);
        }
        error(e) {
          this.isStopped
            ? Rc(
                (function QM(n) {
                  return Ic("E", void 0, n);
                })(e),
                this
              )
            : ((this.isStopped = !0), this._error(e));
        }
        complete() {
          this.isStopped
            ? Rc(ZM, this)
            : ((this.isStopped = !0), this._complete());
        }
        unsubscribe() {
          this.closed ||
            ((this.isStopped = !0),
            super.unsubscribe(),
            (this.destination = null));
        }
        _next(e) {
          this.destination.next(e);
        }
        _error(e) {
          try {
            this.destination.error(e);
          } finally {
            this.unsubscribe();
          }
        }
        _complete() {
          try {
            this.destination.complete();
          } finally {
            this.unsubscribe();
          }
        }
      }
      class kc extends xc {
        constructor(e, t, i) {
          let r;
          if ((super(), ae(e))) r = e;
          else if (e) {
            let s;
            ({ next: r, error: t, complete: i } = e),
              this && xi.useDeprecatedNextContext
                ? ((s = Object.create(e)),
                  (s.unsubscribe = () => this.unsubscribe()))
                : (s = e),
              (r = null == r ? void 0 : r.bind(s)),
              (t = null == t ? void 0 : t.bind(s)),
              (i = null == i ? void 0 : i.bind(s));
          }
          this.destination = {
            next: r ? Fc(r) : ws,
            error: Fc(null != t ? t : Rp),
            complete: i ? Fc(i) : ws,
          };
        }
      }
      function Fc(n, e) {
        return (...t) => {
          try {
            n(...t);
          } catch (i) {
            xi.useDeprecatedSynchronousErrorHandling
              ? (function JM(n) {
                  xi.useDeprecatedSynchronousErrorHandling &&
                    ki &&
                    ((ki.errorThrown = !0), (ki.error = n));
                })(i)
              : Fp(i);
          }
        };
      }
      function Rp(n) {
        throw n;
      }
      function Rc(n, e) {
        const { onStoppedNotification: t } = xi;
        t && Jo.setTimeout(() => t(n, e));
      }
      const e0 = { closed: !0, next: ws, error: Rp, complete: ws },
        Pc =
          ("function" == typeof Symbol && Symbol.observable) || "@@observable";
      function ai(n) {
        return n;
      }
      let fe = (() => {
        class n {
          constructor(t) {
            t && (this._subscribe = t);
          }
          lift(t) {
            const i = new n();
            return (i.source = this), (i.operator = t), i;
          }
          subscribe(t, i, r) {
            const s = (function n0(n) {
              return (
                (n && n instanceof xc) ||
                ((function t0(n) {
                  return n && ae(n.next) && ae(n.error) && ae(n.complete);
                })(n) &&
                  xp(n))
              );
            })(t)
              ? t
              : new kc(t, i, r);
            return (
              ea(() => {
                const { operator: o, source: a } = this;
                s.add(
                  o
                    ? o.call(s, a)
                    : a
                    ? this._subscribe(s)
                    : this._trySubscribe(s)
                );
              }),
              s
            );
          }
          _trySubscribe(t) {
            try {
              return this._subscribe(t);
            } catch (i) {
              t.error(i);
            }
          }
          forEach(t, i) {
            return new (i = Np(i))((r, s) => {
              let o;
              o = this.subscribe(
                (a) => {
                  try {
                    t(a);
                  } catch (l) {
                    s(l), null == o || o.unsubscribe();
                  }
                },
                s,
                r
              );
            });
          }
          _subscribe(t) {
            var i;
            return null === (i = this.source) || void 0 === i
              ? void 0
              : i.subscribe(t);
          }
          [Pc]() {
            return this;
          }
          pipe(...t) {
            return (function Pp(n) {
              return 0 === n.length
                ? ai
                : 1 === n.length
                ? n[0]
                : function (t) {
                    return n.reduce((i, r) => r(i), t);
                  };
            })(t)(this);
          }
          toPromise(t) {
            return new (t = Np(t))((i, r) => {
              let s;
              this.subscribe(
                (o) => (s = o),
                (o) => r(o),
                () => i(s)
              );
            });
          }
        }
        return (n.create = (e) => new n(e)), n;
      })();
      function Np(n) {
        var e;
        return null !== (e = null != n ? n : xi.Promise) && void 0 !== e
          ? e
          : Promise;
      }
      const r0 = Cs(
        (n) =>
          function () {
            n(this),
              (this.name = "ObjectUnsubscribedError"),
              (this.message = "object unsubscribed");
          }
      );
      let le = (() => {
        class n extends fe {
          constructor() {
            super(),
              (this.closed = !1),
              (this.observers = []),
              (this.isStopped = !1),
              (this.hasError = !1),
              (this.thrownError = null);
          }
          lift(t) {
            const i = new Lp(this, this);
            return (i.operator = t), i;
          }
          _throwIfClosed() {
            if (this.closed) throw new r0();
          }
          next(t) {
            ea(() => {
              if ((this._throwIfClosed(), !this.isStopped)) {
                const i = this.observers.slice();
                for (const r of i) r.next(t);
              }
            });
          }
          error(t) {
            ea(() => {
              if ((this._throwIfClosed(), !this.isStopped)) {
                (this.hasError = this.isStopped = !0), (this.thrownError = t);
                const { observers: i } = this;
                for (; i.length; ) i.shift().error(t);
              }
            });
          }
          complete() {
            ea(() => {
              if ((this._throwIfClosed(), !this.isStopped)) {
                this.isStopped = !0;
                const { observers: t } = this;
                for (; t.length; ) t.shift().complete();
              }
            });
          }
          unsubscribe() {
            (this.isStopped = this.closed = !0), (this.observers = null);
          }
          get observed() {
            var t;
            return (
              (null === (t = this.observers) || void 0 === t
                ? void 0
                : t.length) > 0
            );
          }
          _trySubscribe(t) {
            return this._throwIfClosed(), super._trySubscribe(t);
          }
          _subscribe(t) {
            return (
              this._throwIfClosed(),
              this._checkFinalizedStatuses(t),
              this._innerSubscribe(t)
            );
          }
          _innerSubscribe(t) {
            const { hasError: i, isStopped: r, observers: s } = this;
            return i || r ? Ip : (s.push(t), new Le(() => ar(s, t)));
          }
          _checkFinalizedStatuses(t) {
            const { hasError: i, thrownError: r, isStopped: s } = this;
            i ? t.error(r) : s && t.complete();
          }
          asObservable() {
            const t = new fe();
            return (t.source = this), t;
          }
        }
        return (n.create = (e, t) => new Lp(e, t)), n;
      })();
      class Lp extends le {
        constructor(e, t) {
          super(), (this.destination = e), (this.source = t);
        }
        next(e) {
          var t, i;
          null ===
            (i =
              null === (t = this.destination) || void 0 === t
                ? void 0
                : t.next) ||
            void 0 === i ||
            i.call(t, e);
        }
        error(e) {
          var t, i;
          null ===
            (i =
              null === (t = this.destination) || void 0 === t
                ? void 0
                : t.error) ||
            void 0 === i ||
            i.call(t, e);
        }
        complete() {
          var e, t;
          null ===
            (t =
              null === (e = this.destination) || void 0 === e
                ? void 0
                : e.complete) ||
            void 0 === t ||
            t.call(e);
        }
        _subscribe(e) {
          var t, i;
          return null !==
            (i =
              null === (t = this.source) || void 0 === t
                ? void 0
                : t.subscribe(e)) && void 0 !== i
            ? i
            : Ip;
        }
      }
      function Vp(n) {
        return ae(null == n ? void 0 : n.lift);
      }
      function Fe(n) {
        return (e) => {
          if (Vp(e))
            return e.lift(function (t) {
              try {
                return n(t, this);
              } catch (i) {
                this.error(i);
              }
            });
          throw new TypeError("Unable to lift unknown Observable type");
        };
      }
      class De extends xc {
        constructor(e, t, i, r, s) {
          super(e),
            (this.onFinalize = s),
            (this._next = t
              ? function (o) {
                  try {
                    t(o);
                  } catch (a) {
                    e.error(a);
                  }
                }
              : super._next),
            (this._error = r
              ? function (o) {
                  try {
                    r(o);
                  } catch (a) {
                    e.error(a);
                  } finally {
                    this.unsubscribe();
                  }
                }
              : super._error),
            (this._complete = i
              ? function () {
                  try {
                    i();
                  } catch (o) {
                    e.error(o);
                  } finally {
                    this.unsubscribe();
                  }
                }
              : super._complete);
        }
        unsubscribe() {
          var e;
          const { closed: t } = this;
          super.unsubscribe(),
            !t &&
              (null === (e = this.onFinalize) || void 0 === e || e.call(this));
        }
      }
      function re(n, e) {
        return Fe((t, i) => {
          let r = 0;
          t.subscribe(
            new De(i, (s) => {
              i.next(n.call(e, s, r++));
            })
          );
        });
      }
      function Fi(n) {
        return this instanceof Fi ? ((this.v = n), this) : new Fi(n);
      }
      function a0(n, e, t) {
        if (!Symbol.asyncIterator)
          throw new TypeError("Symbol.asyncIterator is not defined.");
        var r,
          i = t.apply(n, e || []),
          s = [];
        return (
          (r = {}),
          o("next"),
          o("throw"),
          o("return"),
          (r[Symbol.asyncIterator] = function () {
            return this;
          }),
          r
        );
        function o(h) {
          i[h] &&
            (r[h] = function (f) {
              return new Promise(function (p, g) {
                s.push([h, f, p, g]) > 1 || a(h, f);
              });
            });
        }
        function a(h, f) {
          try {
            !(function l(h) {
              h.value instanceof Fi
                ? Promise.resolve(h.value.v).then(c, u)
                : d(s[0][2], h);
            })(i[h](f));
          } catch (p) {
            d(s[0][3], p);
          }
        }
        function c(h) {
          a("next", h);
        }
        function u(h) {
          a("throw", h);
        }
        function d(h, f) {
          h(f), s.shift(), s.length && a(s[0][0], s[0][1]);
        }
      }
      function l0(n) {
        if (!Symbol.asyncIterator)
          throw new TypeError("Symbol.asyncIterator is not defined.");
        var t,
          e = n[Symbol.asyncIterator];
        return e
          ? e.call(n)
          : ((n = (function Hp(n) {
              var e = "function" == typeof Symbol && Symbol.iterator,
                t = e && n[e],
                i = 0;
              if (t) return t.call(n);
              if (n && "number" == typeof n.length)
                return {
                  next: function () {
                    return (
                      n && i >= n.length && (n = void 0),
                      { value: n && n[i++], done: !n }
                    );
                  },
                };
              throw new TypeError(
                e
                  ? "Object is not iterable."
                  : "Symbol.iterator is not defined."
              );
            })(n)),
            (t = {}),
            i("next"),
            i("throw"),
            i("return"),
            (t[Symbol.asyncIterator] = function () {
              return this;
            }),
            t);
        function i(s) {
          t[s] =
            n[s] &&
            function (o) {
              return new Promise(function (a, l) {
                !(function r(s, o, a, l) {
                  Promise.resolve(l).then(function (c) {
                    s({ value: c, done: a });
                  }, o);
                })(a, l, (o = n[s](o)).done, o.value);
              });
            };
        }
      }
      const Lc = (n) =>
        n && "number" == typeof n.length && "function" != typeof n;
      function Up(n) {
        return ae(null == n ? void 0 : n.then);
      }
      function $p(n) {
        return ae(n[Pc]);
      }
      function zp(n) {
        return (
          Symbol.asyncIterator &&
          ae(null == n ? void 0 : n[Symbol.asyncIterator])
        );
      }
      function Gp(n) {
        return new TypeError(
          `You provided ${
            null !== n && "object" == typeof n ? "an invalid object" : `'${n}'`
          } where a stream was expected. You can provide an Observable, Promise, ReadableStream, Array, AsyncIterable, or Iterable.`
        );
      }
      const qp = (function u0() {
        return "function" == typeof Symbol && Symbol.iterator
          ? Symbol.iterator
          : "@@iterator";
      })();
      function Wp(n) {
        return ae(null == n ? void 0 : n[qp]);
      }
      function Kp(n) {
        return a0(this, arguments, function* () {
          const t = n.getReader();
          try {
            for (;;) {
              const { value: i, done: r } = yield Fi(t.read());
              if (r) return yield Fi(void 0);
              yield yield Fi(i);
            }
          } finally {
            t.releaseLock();
          }
        });
      }
      function Yp(n) {
        return ae(null == n ? void 0 : n.getReader);
      }
      function St(n) {
        if (n instanceof fe) return n;
        if (null != n) {
          if ($p(n))
            return (function d0(n) {
              return new fe((e) => {
                const t = n[Pc]();
                if (ae(t.subscribe)) return t.subscribe(e);
                throw new TypeError(
                  "Provided object does not correctly implement Symbol.observable"
                );
              });
            })(n);
          if (Lc(n))
            return (function h0(n) {
              return new fe((e) => {
                for (let t = 0; t < n.length && !e.closed; t++) e.next(n[t]);
                e.complete();
              });
            })(n);
          if (Up(n))
            return (function f0(n) {
              return new fe((e) => {
                n.then(
                  (t) => {
                    e.closed || (e.next(t), e.complete());
                  },
                  (t) => e.error(t)
                ).then(null, Fp);
              });
            })(n);
          if (zp(n)) return Zp(n);
          if (Wp(n))
            return (function p0(n) {
              return new fe((e) => {
                for (const t of n) if ((e.next(t), e.closed)) return;
                e.complete();
              });
            })(n);
          if (Yp(n))
            return (function g0(n) {
              return Zp(Kp(n));
            })(n);
        }
        throw Gp(n);
      }
      function Zp(n) {
        return new fe((e) => {
          (function m0(n, e) {
            var t, i, r, s;
            return (function s0(n, e, t, i) {
              return new (t || (t = Promise))(function (s, o) {
                function a(u) {
                  try {
                    c(i.next(u));
                  } catch (d) {
                    o(d);
                  }
                }
                function l(u) {
                  try {
                    c(i.throw(u));
                  } catch (d) {
                    o(d);
                  }
                }
                function c(u) {
                  u.done
                    ? s(u.value)
                    : (function r(s) {
                        return s instanceof t
                          ? s
                          : new t(function (o) {
                              o(s);
                            });
                      })(u.value).then(a, l);
                }
                c((i = i.apply(n, e || [])).next());
              });
            })(this, void 0, void 0, function* () {
              try {
                for (t = l0(n); !(i = yield t.next()).done; )
                  if ((e.next(i.value), e.closed)) return;
              } catch (o) {
                r = { error: o };
              } finally {
                try {
                  i && !i.done && (s = t.return) && (yield s.call(t));
                } finally {
                  if (r) throw r.error;
                }
              }
              e.complete();
            });
          })(n, e).catch((t) => e.error(t));
        });
      }
      function Hn(n, e, t, i = 0, r = !1) {
        const s = e.schedule(function () {
          t(), r ? n.add(this.schedule(null, i)) : this.unsubscribe();
        }, i);
        if ((n.add(s), !r)) return s;
      }
      function Ke(n, e, t = 1 / 0) {
        return ae(e)
          ? Ke((i, r) => re((s, o) => e(i, s, r, o))(St(n(i, r))), t)
          : ("number" == typeof e && (t = e),
            Fe((i, r) =>
              (function _0(n, e, t, i, r, s, o, a) {
                const l = [];
                let c = 0,
                  u = 0,
                  d = !1;
                const h = () => {
                    d && !l.length && !c && e.complete();
                  },
                  f = (g) => (c < i ? p(g) : l.push(g)),
                  p = (g) => {
                    s && e.next(g), c++;
                    let y = !1;
                    St(t(g, u++)).subscribe(
                      new De(
                        e,
                        (v) => {
                          null == r || r(v), s ? f(v) : e.next(v);
                        },
                        () => {
                          y = !0;
                        },
                        void 0,
                        () => {
                          if (y)
                            try {
                              for (c--; l.length && c < i; ) {
                                const v = l.shift();
                                o ? Hn(e, o, () => p(v)) : p(v);
                              }
                              h();
                            } catch (v) {
                              e.error(v);
                            }
                        }
                      )
                    );
                  };
                return (
                  n.subscribe(
                    new De(e, f, () => {
                      (d = !0), h();
                    })
                  ),
                  () => {
                    null == a || a();
                  }
                );
              })(i, r, n, t)
            ));
      }
      function Ds(n = 1 / 0) {
        return Ke(ai, n);
      }
      const wn = new fe((n) => n.complete());
      function Qp(n) {
        return n && ae(n.schedule);
      }
      function Vc(n) {
        return n[n.length - 1];
      }
      function Xp(n) {
        return ae(Vc(n)) ? n.pop() : void 0;
      }
      function Es(n) {
        return Qp(Vc(n)) ? n.pop() : void 0;
      }
      function Jp(n, e = 0) {
        return Fe((t, i) => {
          t.subscribe(
            new De(
              i,
              (r) => Hn(i, n, () => i.next(r), e),
              () => Hn(i, n, () => i.complete(), e),
              (r) => Hn(i, n, () => i.error(r), e)
            )
          );
        });
      }
      function eg(n, e = 0) {
        return Fe((t, i) => {
          i.add(n.schedule(() => t.subscribe(i), e));
        });
      }
      function tg(n, e) {
        if (!n) throw new Error("Iterable cannot be null");
        return new fe((t) => {
          Hn(t, e, () => {
            const i = n[Symbol.asyncIterator]();
            Hn(
              t,
              e,
              () => {
                i.next().then((r) => {
                  r.done ? t.complete() : t.next(r.value);
                });
              },
              0,
              !0
            );
          });
        });
      }
      function et(n, e) {
        return e
          ? (function M0(n, e) {
              if (null != n) {
                if ($p(n))
                  return (function b0(n, e) {
                    return St(n).pipe(eg(e), Jp(e));
                  })(n, e);
                if (Lc(n))
                  return (function w0(n, e) {
                    return new fe((t) => {
                      let i = 0;
                      return e.schedule(function () {
                        i === n.length
                          ? t.complete()
                          : (t.next(n[i++]), t.closed || this.schedule());
                      });
                    });
                  })(n, e);
                if (Up(n))
                  return (function C0(n, e) {
                    return St(n).pipe(eg(e), Jp(e));
                  })(n, e);
                if (zp(n)) return tg(n, e);
                if (Wp(n))
                  return (function D0(n, e) {
                    return new fe((t) => {
                      let i;
                      return (
                        Hn(t, e, () => {
                          (i = n[qp]()),
                            Hn(
                              t,
                              e,
                              () => {
                                let r, s;
                                try {
                                  ({ value: r, done: s } = i.next());
                                } catch (o) {
                                  return void t.error(o);
                                }
                                s ? t.complete() : t.next(r);
                              },
                              0,
                              !0
                            );
                        }),
                        () => ae(null == i ? void 0 : i.return) && i.return()
                      );
                    });
                  })(n, e);
                if (Yp(n))
                  return (function E0(n, e) {
                    return tg(Kp(n), e);
                  })(n, e);
              }
              throw Gp(n);
            })(n, e)
          : St(n);
      }
      function lr(...n) {
        const e = Es(n),
          t = (function v0(n, e) {
            return "number" == typeof Vc(n) ? n.pop() : e;
          })(n, 1 / 0),
          i = n;
        return i.length ? (1 === i.length ? St(i[0]) : Ds(t)(et(i, e))) : wn;
      }
      function Un(n) {
        return n <= 0
          ? () => wn
          : Fe((e, t) => {
              let i = 0;
              e.subscribe(
                new De(t, (r) => {
                  ++i <= n && (t.next(r), n <= i && t.complete());
                })
              );
            });
      }
      function Bc(n, e, ...t) {
        return !0 === e
          ? (n(), null)
          : !1 === e
          ? null
          : e(...t)
              .pipe(Un(1))
              .subscribe(() => n());
      }
      function me(n) {
        for (let e in n) if (n[e] === me) return e;
        throw Error("Could not find renamed property on target object.");
      }
      function jc(n, e) {
        for (const t in e)
          e.hasOwnProperty(t) && !n.hasOwnProperty(t) && (n[t] = e[t]);
      }
      function de(n) {
        if ("string" == typeof n) return n;
        if (Array.isArray(n)) return "[" + n.map(de).join(", ") + "]";
        if (null == n) return "" + n;
        if (n.overriddenName) return `${n.overriddenName}`;
        if (n.name) return `${n.name}`;
        const e = n.toString();
        if (null == e) return "" + e;
        const t = e.indexOf("\n");
        return -1 === t ? e : e.substring(0, t);
      }
      function Hc(n, e) {
        return null == n || "" === n
          ? null === e
            ? ""
            : e
          : null == e || "" === e
          ? n
          : n + " " + e;
      }
      const A0 = me({ __forward_ref__: me });
      function _e(n) {
        return (
          (n.__forward_ref__ = _e),
          (n.toString = function () {
            return de(this());
          }),
          n
        );
      }
      function z(n) {
        return ng(n) ? n() : n;
      }
      function ng(n) {
        return (
          "function" == typeof n &&
          n.hasOwnProperty(A0) &&
          n.__forward_ref__ === _e
        );
      }
      class ne extends Error {
        constructor(e, t) {
          super(
            (function Uc(n, e) {
              return `NG0${Math.abs(n)}${e ? ": " + e : ""}`;
            })(e, t)
          ),
            (this.code = e);
        }
      }
      function B(n) {
        return "string" == typeof n ? n : null == n ? "" : String(n);
      }
      function ht(n) {
        return "function" == typeof n
          ? n.name || n.toString()
          : "object" == typeof n && null != n && "function" == typeof n.type
          ? n.type.name || n.type.toString()
          : B(n);
      }
      function ta(n, e) {
        const t = e ? ` in ${e}` : "";
        throw new ne(-201, `No provider for ${ht(n)} found${t}`);
      }
      function Tt(n, e) {
        null == n &&
          (function we(n, e, t, i) {
            throw new Error(
              `ASSERTION ERROR: ${n}` +
                (null == i ? "" : ` [Expected=> ${t} ${i} ${e} <=Actual]`)
            );
          })(e, n, null, "!=");
      }
      function I(n) {
        return {
          token: n.token,
          providedIn: n.providedIn || null,
          factory: n.factory,
          value: void 0,
        };
      }
      function ce(n) {
        return { providers: n.providers || [], imports: n.imports || [] };
      }
      function $c(n) {
        return ig(n, na) || ig(n, sg);
      }
      function ig(n, e) {
        return n.hasOwnProperty(e) ? n[e] : null;
      }
      function rg(n) {
        return n && (n.hasOwnProperty(zc) || n.hasOwnProperty(R0))
          ? n[zc]
          : null;
      }
      const na = me({ ɵprov: me }),
        zc = me({ ɵinj: me }),
        sg = me({ ngInjectableDef: me }),
        R0 = me({ ngInjectorDef: me });
      var U = (() => (
        ((U = U || {})[(U.Default = 0)] = "Default"),
        (U[(U.Host = 1)] = "Host"),
        (U[(U.Self = 2)] = "Self"),
        (U[(U.SkipSelf = 4)] = "SkipSelf"),
        (U[(U.Optional = 8)] = "Optional"),
        U
      ))();
      let Gc;
      function li(n) {
        const e = Gc;
        return (Gc = n), e;
      }
      function og(n, e, t) {
        const i = $c(n);
        return i && "root" == i.providedIn
          ? void 0 === i.value
            ? (i.value = i.factory())
            : i.value
          : t & U.Optional
          ? null
          : void 0 !== e
          ? e
          : void ta(de(n), "Injector");
      }
      function ci(n) {
        return { toString: n }.toString();
      }
      var on = (() => (
          ((on = on || {})[(on.OnPush = 0)] = "OnPush"),
          (on[(on.Default = 1)] = "Default"),
          on
        ))(),
        an = (() => {
          return (
            ((n = an || (an = {}))[(n.Emulated = 0)] = "Emulated"),
            (n[(n.None = 2)] = "None"),
            (n[(n.ShadowDom = 3)] = "ShadowDom"),
            an
          );
          var n;
        })();
      const N0 = "undefined" != typeof globalThis && globalThis,
        L0 = "undefined" != typeof window && window,
        V0 =
          "undefined" != typeof self &&
          "undefined" != typeof WorkerGlobalScope &&
          self instanceof WorkerGlobalScope &&
          self,
        pe = N0 || ("undefined" != typeof global && global) || L0 || V0,
        cr = {},
        ye = [],
        ia = me({ ɵcmp: me }),
        qc = me({ ɵdir: me }),
        Wc = me({ ɵpipe: me }),
        ag = me({ ɵmod: me }),
        zn = me({ ɵfac: me }),
        Ms = me({ __NG_ELEMENT_ID__: me });
      let B0 = 0;
      function Dn(n) {
        return ci(() => {
          const t = {},
            i = {
              type: n.type,
              providersResolver: null,
              decls: n.decls,
              vars: n.vars,
              factory: null,
              template: n.template || null,
              consts: n.consts || null,
              ngContentSelectors: n.ngContentSelectors,
              hostBindings: n.hostBindings || null,
              hostVars: n.hostVars || 0,
              hostAttrs: n.hostAttrs || null,
              contentQueries: n.contentQueries || null,
              declaredInputs: t,
              inputs: null,
              outputs: null,
              exportAs: n.exportAs || null,
              onPush: n.changeDetection === on.OnPush,
              directiveDefs: null,
              pipeDefs: null,
              selectors: n.selectors || ye,
              viewQuery: n.viewQuery || null,
              features: n.features || null,
              data: n.data || {},
              encapsulation: n.encapsulation || an.Emulated,
              id: "c",
              styles: n.styles || ye,
              _: null,
              setInput: null,
              schemas: n.schemas || null,
              tView: null,
            },
            r = n.directives,
            s = n.features,
            o = n.pipes;
          return (
            (i.id += B0++),
            (i.inputs = dg(n.inputs, t)),
            (i.outputs = dg(n.outputs)),
            s && s.forEach((a) => a(i)),
            (i.directiveDefs = r
              ? () => ("function" == typeof r ? r() : r).map(lg)
              : null),
            (i.pipeDefs = o
              ? () => ("function" == typeof o ? o() : o).map(cg)
              : null),
            i
          );
        });
      }
      function lg(n) {
        return (
          st(n) ||
          (function ui(n) {
            return n[qc] || null;
          })(n)
        );
      }
      function cg(n) {
        return (function Ri(n) {
          return n[Wc] || null;
        })(n);
      }
      const ug = {};
      function he(n) {
        return ci(() => {
          const e = {
            type: n.type,
            bootstrap: n.bootstrap || ye,
            declarations: n.declarations || ye,
            imports: n.imports || ye,
            exports: n.exports || ye,
            transitiveCompileScopes: null,
            schemas: n.schemas || null,
            id: n.id || null,
          };
          return null != n.id && (ug[n.id] = n.type), e;
        });
      }
      function dg(n, e) {
        if (null == n) return cr;
        const t = {};
        for (const i in n)
          if (n.hasOwnProperty(i)) {
            let r = n[i],
              s = r;
            Array.isArray(r) && ((s = r[1]), (r = r[0])),
              (t[r] = i),
              e && (e[r] = s);
          }
        return t;
      }
      const x = Dn;
      function st(n) {
        return n[ia] || null;
      }
      function zt(n, e) {
        const t = n[ag] || null;
        if (!t && !0 === e)
          throw new Error(`Type ${de(n)} does not have '\u0275mod' property.`);
        return t;
      }
      const G = 11;
      function En(n) {
        return Array.isArray(n) && "object" == typeof n[1];
      }
      function cn(n) {
        return Array.isArray(n) && !0 === n[1];
      }
      function Zc(n) {
        return 0 != (8 & n.flags);
      }
      function aa(n) {
        return 2 == (2 & n.flags);
      }
      function la(n) {
        return 1 == (1 & n.flags);
      }
      function un(n) {
        return null !== n.template;
      }
      function G0(n) {
        return 0 != (512 & n[2]);
      }
      function Vi(n, e) {
        return n.hasOwnProperty(zn) ? n[zn] : null;
      }
      class K0 {
        constructor(e, t, i) {
          (this.previousValue = e),
            (this.currentValue = t),
            (this.firstChange = i);
        }
        isFirstChange() {
          return this.firstChange;
        }
      }
      function at() {
        return fg;
      }
      function fg(n) {
        return n.type.prototype.ngOnChanges && (n.setInput = Z0), Y0;
      }
      function Y0() {
        const n = gg(this),
          e = null == n ? void 0 : n.current;
        if (e) {
          const t = n.previous;
          if (t === cr) n.previous = e;
          else for (let i in e) t[i] = e[i];
          (n.current = null), this.ngOnChanges(e);
        }
      }
      function Z0(n, e, t, i) {
        const r =
            gg(n) ||
            (function Q0(n, e) {
              return (n[pg] = e);
            })(n, { previous: cr, current: null }),
          s = r.current || (r.current = {}),
          o = r.previous,
          a = this.declaredInputs[t],
          l = o[a];
        (s[a] = new K0(l && l.currentValue, e, o === cr)), (n[i] = e);
      }
      at.ngInherit = !0;
      const pg = "__ngSimpleChanges__";
      function gg(n) {
        return n[pg] || null;
      }
      let Jc;
      function Re(n) {
        return !!n.listen;
      }
      const yg = {
        createRenderer: (n, e) =>
          (function eu() {
            return void 0 !== Jc
              ? Jc
              : "undefined" != typeof document
              ? document
              : void 0;
          })(),
      };
      function He(n) {
        for (; Array.isArray(n); ) n = n[0];
        return n;
      }
      function ca(n, e) {
        return He(e[n]);
      }
      function Wt(n, e) {
        return He(e[n.index]);
      }
      function tu(n, e) {
        return n.data[e];
      }
      function It(n, e) {
        const t = e[n];
        return En(t) ? t : t[0];
      }
      function vg(n) {
        return 4 == (4 & n[2]);
      }
      function nu(n) {
        return 128 == (128 & n[2]);
      }
      function di(n, e) {
        return null == e ? null : n[e];
      }
      function bg(n) {
        n[18] = 0;
      }
      function iu(n, e) {
        n[5] += e;
        let t = n,
          i = n[3];
        for (
          ;
          null !== i && ((1 === e && 1 === t[5]) || (-1 === e && 0 === t[5]));

        )
          (i[5] += e), (t = i), (i = i[3]);
      }
      const V = {
        lFrame: Tg(null),
        bindingsEnabled: !0,
        isInCheckNoChangesMode: !1,
      };
      function Cg() {
        return V.bindingsEnabled;
      }
      function C() {
        return V.lFrame.lView;
      }
      function ie() {
        return V.lFrame.tView;
      }
      function nt(n) {
        return (V.lFrame.contextLView = n), n[8];
      }
      function Ye() {
        let n = wg();
        for (; null !== n && 64 === n.type; ) n = n.parent;
        return n;
      }
      function wg() {
        return V.lFrame.currentTNode;
      }
      function Mn(n, e) {
        const t = V.lFrame;
        (t.currentTNode = n), (t.isParent = e);
      }
      function ru() {
        return V.lFrame.isParent;
      }
      function su() {
        V.lFrame.isParent = !1;
      }
      function ua() {
        return V.isInCheckNoChangesMode;
      }
      function da(n) {
        V.isInCheckNoChangesMode = n;
      }
      function gr() {
        return V.lFrame.bindingIndex++;
      }
      function qn(n) {
        const e = V.lFrame,
          t = e.bindingIndex;
        return (e.bindingIndex = e.bindingIndex + n), t;
      }
      function dS(n, e) {
        const t = V.lFrame;
        (t.bindingIndex = t.bindingRootIndex = n), ou(e);
      }
      function ou(n) {
        V.lFrame.currentDirectiveIndex = n;
      }
      function Mg() {
        return V.lFrame.currentQueryIndex;
      }
      function lu(n) {
        V.lFrame.currentQueryIndex = n;
      }
      function fS(n) {
        const e = n[1];
        return 2 === e.type ? e.declTNode : 1 === e.type ? n[6] : null;
      }
      function Sg(n, e, t) {
        if (t & U.SkipSelf) {
          let r = e,
            s = n;
          for (
            ;
            !((r = r.parent),
            null !== r ||
              t & U.Host ||
              ((r = fS(s)), null === r || ((s = s[15]), 10 & r.type)));

          );
          if (null === r) return !1;
          (e = r), (n = s);
        }
        const i = (V.lFrame = Ag());
        return (i.currentTNode = e), (i.lView = n), !0;
      }
      function ha(n) {
        const e = Ag(),
          t = n[1];
        (V.lFrame = e),
          (e.currentTNode = t.firstChild),
          (e.lView = n),
          (e.tView = t),
          (e.contextLView = n),
          (e.bindingIndex = t.bindingStartIndex),
          (e.inI18n = !1);
      }
      function Ag() {
        const n = V.lFrame,
          e = null === n ? null : n.child;
        return null === e ? Tg(n) : e;
      }
      function Tg(n) {
        const e = {
          currentTNode: null,
          isParent: !0,
          lView: null,
          tView: null,
          selectedIndex: -1,
          contextLView: null,
          elementDepthCount: 0,
          currentNamespace: null,
          currentDirectiveIndex: -1,
          bindingRootIndex: -1,
          bindingIndex: -1,
          currentQueryIndex: 0,
          parent: n,
          child: null,
          inI18n: !1,
        };
        return null !== n && (n.child = e), e;
      }
      function Og() {
        const n = V.lFrame;
        return (
          (V.lFrame = n.parent), (n.currentTNode = null), (n.lView = null), n
        );
      }
      const Ig = Og;
      function fa() {
        const n = Og();
        (n.isParent = !0),
          (n.tView = null),
          (n.selectedIndex = -1),
          (n.contextLView = null),
          (n.elementDepthCount = 0),
          (n.currentDirectiveIndex = -1),
          (n.currentNamespace = null),
          (n.bindingRootIndex = -1),
          (n.bindingIndex = -1),
          (n.currentQueryIndex = 0);
      }
      function pt() {
        return V.lFrame.selectedIndex;
      }
      function hi(n) {
        V.lFrame.selectedIndex = n;
      }
      function Pe() {
        const n = V.lFrame;
        return tu(n.tView, n.selectedIndex);
      }
      function pa(n, e) {
        for (let t = e.directiveStart, i = e.directiveEnd; t < i; t++) {
          const s = n.data[t].type.prototype,
            {
              ngAfterContentInit: o,
              ngAfterContentChecked: a,
              ngAfterViewInit: l,
              ngAfterViewChecked: c,
              ngOnDestroy: u,
            } = s;
          o && (n.contentHooks || (n.contentHooks = [])).push(-t, o),
            a &&
              ((n.contentHooks || (n.contentHooks = [])).push(t, a),
              (n.contentCheckHooks || (n.contentCheckHooks = [])).push(t, a)),
            l && (n.viewHooks || (n.viewHooks = [])).push(-t, l),
            c &&
              ((n.viewHooks || (n.viewHooks = [])).push(t, c),
              (n.viewCheckHooks || (n.viewCheckHooks = [])).push(t, c)),
            null != u && (n.destroyHooks || (n.destroyHooks = [])).push(t, u);
        }
      }
      function ga(n, e, t) {
        xg(n, e, 3, t);
      }
      function ma(n, e, t, i) {
        (3 & n[2]) === t && xg(n, e, t, i);
      }
      function cu(n, e) {
        let t = n[2];
        (3 & t) === e && ((t &= 2047), (t += 1), (n[2] = t));
      }
      function xg(n, e, t, i) {
        const s = null != i ? i : -1,
          o = e.length - 1;
        let a = 0;
        for (let l = void 0 !== i ? 65535 & n[18] : 0; l < o; l++)
          if ("number" == typeof e[l + 1]) {
            if (((a = e[l]), null != i && a >= i)) break;
          } else
            e[l] < 0 && (n[18] += 65536),
              (a < s || -1 == s) &&
                (wS(n, t, e, l), (n[18] = (4294901760 & n[18]) + l + 2)),
              l++;
      }
      function wS(n, e, t, i) {
        const r = t[i] < 0,
          s = t[i + 1],
          a = n[r ? -t[i] : t[i]];
        if (r) {
          if (n[2] >> 11 < n[18] >> 16 && (3 & n[2]) === e) {
            n[2] += 2048;
            try {
              s.call(a);
            } finally {
            }
          }
        } else
          try {
            s.call(a);
          } finally {
          }
      }
      class Is {
        constructor(e, t, i) {
          (this.factory = e),
            (this.resolving = !1),
            (this.canSeeViewProviders = t),
            (this.injectImpl = i);
        }
      }
      function _a(n, e, t) {
        const i = Re(n);
        let r = 0;
        for (; r < t.length; ) {
          const s = t[r];
          if ("number" == typeof s) {
            if (0 !== s) break;
            r++;
            const o = t[r++],
              a = t[r++],
              l = t[r++];
            i ? n.setAttribute(e, a, l, o) : e.setAttributeNS(o, a, l);
          } else {
            const o = s,
              a = t[++r];
            du(o)
              ? i && n.setProperty(e, o, a)
              : i
              ? n.setAttribute(e, o, a)
              : e.setAttribute(o, a),
              r++;
          }
        }
        return r;
      }
      function kg(n) {
        return 3 === n || 4 === n || 6 === n;
      }
      function du(n) {
        return 64 === n.charCodeAt(0);
      }
      function ya(n, e) {
        if (null !== e && 0 !== e.length)
          if (null === n || 0 === n.length) n = e.slice();
          else {
            let t = -1;
            for (let i = 0; i < e.length; i++) {
              const r = e[i];
              "number" == typeof r
                ? (t = r)
                : 0 === t ||
                  Fg(n, t, r, null, -1 === t || 2 === t ? e[++i] : null);
            }
          }
        return n;
      }
      function Fg(n, e, t, i, r) {
        let s = 0,
          o = n.length;
        if (-1 === e) o = -1;
        else
          for (; s < n.length; ) {
            const a = n[s++];
            if ("number" == typeof a) {
              if (a === e) {
                o = -1;
                break;
              }
              if (a > e) {
                o = s - 1;
                break;
              }
            }
          }
        for (; s < n.length; ) {
          const a = n[s];
          if ("number" == typeof a) break;
          if (a === t) {
            if (null === i) return void (null !== r && (n[s + 1] = r));
            if (i === n[s + 1]) return void (n[s + 2] = r);
          }
          s++, null !== i && s++, null !== r && s++;
        }
        -1 !== o && (n.splice(o, 0, e), (s = o + 1)),
          n.splice(s++, 0, t),
          null !== i && n.splice(s++, 0, i),
          null !== r && n.splice(s++, 0, r);
      }
      function Rg(n) {
        return -1 !== n;
      }
      function mr(n) {
        return 32767 & n;
      }
      function _r(n, e) {
        let t = (function AS(n) {
            return n >> 16;
          })(n),
          i = e;
        for (; t > 0; ) (i = i[15]), t--;
        return i;
      }
      let hu = !0;
      function va(n) {
        const e = hu;
        return (hu = n), e;
      }
      let TS = 0;
      function ks(n, e) {
        const t = pu(n, e);
        if (-1 !== t) return t;
        const i = e[1];
        i.firstCreatePass &&
          ((n.injectorIndex = e.length),
          fu(i.data, n),
          fu(e, null),
          fu(i.blueprint, null));
        const r = ba(n, e),
          s = n.injectorIndex;
        if (Rg(r)) {
          const o = mr(r),
            a = _r(r, e),
            l = a[1].data;
          for (let c = 0; c < 8; c++) e[s + c] = a[o + c] | l[o + c];
        }
        return (e[s + 8] = r), s;
      }
      function fu(n, e) {
        n.push(0, 0, 0, 0, 0, 0, 0, 0, e);
      }
      function pu(n, e) {
        return -1 === n.injectorIndex ||
          (n.parent && n.parent.injectorIndex === n.injectorIndex) ||
          null === e[n.injectorIndex + 8]
          ? -1
          : n.injectorIndex;
      }
      function ba(n, e) {
        if (n.parent && -1 !== n.parent.injectorIndex)
          return n.parent.injectorIndex;
        let t = 0,
          i = null,
          r = e;
        for (; null !== r; ) {
          const s = r[1],
            o = s.type;
          if (((i = 2 === o ? s.declTNode : 1 === o ? r[6] : null), null === i))
            return -1;
          if ((t++, (r = r[15]), -1 !== i.injectorIndex))
            return i.injectorIndex | (t << 16);
        }
        return -1;
      }
      function Ca(n, e, t) {
        !(function OS(n, e, t) {
          let i;
          "string" == typeof t
            ? (i = t.charCodeAt(0) || 0)
            : t.hasOwnProperty(Ms) && (i = t[Ms]),
            null == i && (i = t[Ms] = TS++);
          const r = 255 & i;
          e.data[n + (r >> 5)] |= 1 << r;
        })(n, e, t);
      }
      function Lg(n, e, t) {
        if (t & U.Optional) return n;
        ta(e, "NodeInjector");
      }
      function Vg(n, e, t, i) {
        if (
          (t & U.Optional && void 0 === i && (i = null),
          0 == (t & (U.Self | U.Host)))
        ) {
          const r = n[9],
            s = li(void 0);
          try {
            return r ? r.get(e, i, t & U.Optional) : og(e, i, t & U.Optional);
          } finally {
            li(s);
          }
        }
        return Lg(i, e, t);
      }
      function Bg(n, e, t, i = U.Default, r) {
        if (null !== n) {
          const s = (function FS(n) {
            if ("string" == typeof n) return n.charCodeAt(0) || 0;
            const e = n.hasOwnProperty(Ms) ? n[Ms] : void 0;
            return "number" == typeof e ? (e >= 0 ? 255 & e : xS) : e;
          })(t);
          if ("function" == typeof s) {
            if (!Sg(e, n, i)) return i & U.Host ? Lg(r, t, i) : Vg(e, t, i, r);
            try {
              const o = s(i);
              if (null != o || i & U.Optional) return o;
              ta(t);
            } finally {
              Ig();
            }
          } else if ("number" == typeof s) {
            let o = null,
              a = pu(n, e),
              l = -1,
              c = i & U.Host ? e[16][6] : null;
            for (
              (-1 === a || i & U.SkipSelf) &&
              ((l = -1 === a ? ba(n, e) : e[a + 8]),
              -1 !== l && Ug(i, !1)
                ? ((o = e[1]), (a = mr(l)), (e = _r(l, e)))
                : (a = -1));
              -1 !== a;

            ) {
              const u = e[1];
              if (Hg(s, a, u.data)) {
                const d = kS(a, e, t, o, i, c);
                if (d !== jg) return d;
              }
              (l = e[a + 8]),
                -1 !== l && Ug(i, e[1].data[a + 8] === c) && Hg(s, a, e)
                  ? ((o = u), (a = mr(l)), (e = _r(l, e)))
                  : (a = -1);
            }
          }
        }
        return Vg(e, t, i, r);
      }
      const jg = {};
      function xS() {
        return new yr(Ye(), C());
      }
      function kS(n, e, t, i, r, s) {
        const o = e[1],
          a = o.data[n + 8],
          u = wa(
            a,
            o,
            t,
            null == i ? aa(a) && hu : i != o && 0 != (3 & a.type),
            r & U.Host && s === a
          );
        return null !== u ? Fs(e, o, u, a) : jg;
      }
      function wa(n, e, t, i, r) {
        const s = n.providerIndexes,
          o = e.data,
          a = 1048575 & s,
          l = n.directiveStart,
          u = s >> 20,
          h = r ? a + u : n.directiveEnd;
        for (let f = i ? a : a + u; f < h; f++) {
          const p = o[f];
          if ((f < l && t === p) || (f >= l && p.type === t)) return f;
        }
        if (r) {
          const f = o[l];
          if (f && un(f) && f.type === t) return l;
        }
        return null;
      }
      function Fs(n, e, t, i) {
        let r = n[t];
        const s = e.data;
        if (
          (function DS(n) {
            return n instanceof Is;
          })(r)
        ) {
          const o = r;
          o.resolving &&
            (function T0(n, e) {
              const t = e ? `. Dependency path: ${e.join(" > ")} > ${n}` : "";
              throw new ne(
                -200,
                `Circular dependency in DI detected for ${n}${t}`
              );
            })(ht(s[t]));
          const a = va(o.canSeeViewProviders);
          o.resolving = !0;
          const l = o.injectImpl ? li(o.injectImpl) : null;
          Sg(n, i, U.Default);
          try {
            (r = n[t] = o.factory(void 0, s, n, i)),
              e.firstCreatePass &&
                t >= i.directiveStart &&
                (function CS(n, e, t) {
                  const {
                    ngOnChanges: i,
                    ngOnInit: r,
                    ngDoCheck: s,
                  } = e.type.prototype;
                  if (i) {
                    const o = fg(e);
                    (t.preOrderHooks || (t.preOrderHooks = [])).push(n, o),
                      (
                        t.preOrderCheckHooks || (t.preOrderCheckHooks = [])
                      ).push(n, o);
                  }
                  r &&
                    (t.preOrderHooks || (t.preOrderHooks = [])).push(0 - n, r),
                    s &&
                      ((t.preOrderHooks || (t.preOrderHooks = [])).push(n, s),
                      (
                        t.preOrderCheckHooks || (t.preOrderCheckHooks = [])
                      ).push(n, s));
                })(t, s[t], e);
          } finally {
            null !== l && li(l), va(a), (o.resolving = !1), Ig();
          }
        }
        return r;
      }
      function Hg(n, e, t) {
        return !!(t[e + (n >> 5)] & (1 << n));
      }
      function Ug(n, e) {
        return !(n & U.Self || (n & U.Host && e));
      }
      class yr {
        constructor(e, t) {
          (this._tNode = e), (this._lView = t);
        }
        get(e, t, i) {
          return Bg(this._tNode, this._lView, e, i, t);
        }
      }
      function gt(n) {
        return ci(() => {
          const e = n.prototype.constructor,
            t = e[zn] || gu(e),
            i = Object.prototype;
          let r = Object.getPrototypeOf(n.prototype).constructor;
          for (; r && r !== i; ) {
            const s = r[zn] || gu(r);
            if (s && s !== t) return s;
            r = Object.getPrototypeOf(r);
          }
          return (s) => new s();
        });
      }
      function gu(n) {
        return ng(n)
          ? () => {
              const e = gu(z(n));
              return e && e();
            }
          : Vi(n);
      }
      function Bi(n) {
        return (function IS(n, e) {
          if ("class" === e) return n.classes;
          if ("style" === e) return n.styles;
          const t = n.attrs;
          if (t) {
            const i = t.length;
            let r = 0;
            for (; r < i; ) {
              const s = t[r];
              if (kg(s)) break;
              if (0 === s) r += 2;
              else if ("number" == typeof s)
                for (r++; r < i && "string" == typeof t[r]; ) r++;
              else {
                if (s === e) return t[r + 1];
                r += 2;
              }
            }
          }
          return null;
        })(Ye(), n);
      }
      const br = "__parameters__";
      function wr(n, e, t) {
        return ci(() => {
          const i = (function mu(n) {
            return function (...t) {
              if (n) {
                const i = n(...t);
                for (const r in i) this[r] = i[r];
              }
            };
          })(e);
          function r(...s) {
            if (this instanceof r) return i.apply(this, s), this;
            const o = new r(...s);
            return (a.annotation = o), a;
            function a(l, c, u) {
              const d = l.hasOwnProperty(br)
                ? l[br]
                : Object.defineProperty(l, br, { value: [] })[br];
              for (; d.length <= u; ) d.push(null);
              return (d[u] = d[u] || []).push(o), l;
            }
          }
          return (
            t && (r.prototype = Object.create(t.prototype)),
            (r.prototype.ngMetadataName = n),
            (r.annotationCls = r),
            r
          );
        });
      }
      class T {
        constructor(e, t) {
          (this._desc = e),
            (this.ngMetadataName = "InjectionToken"),
            (this.ɵprov = void 0),
            "number" == typeof t
              ? (this.__NG_ELEMENT_ID__ = t)
              : void 0 !== t &&
                (this.ɵprov = I({
                  token: this,
                  providedIn: t.providedIn || "root",
                  factory: t.factory,
                }));
        }
        toString() {
          return `InjectionToken ${this._desc}`;
        }
      }
      const PS = new T("AnalyzeForEntryComponents");
      function Kt(n, e) {
        void 0 === e && (e = n);
        for (let t = 0; t < n.length; t++) {
          let i = n[t];
          Array.isArray(i)
            ? (e === n && (e = n.slice(0, t)), Kt(i, e))
            : e !== n && e.push(i);
        }
        return e;
      }
      function Sn(n, e) {
        n.forEach((t) => (Array.isArray(t) ? Sn(t, e) : e(t)));
      }
      function zg(n, e, t) {
        e >= n.length ? n.push(t) : n.splice(e, 0, t);
      }
      function Da(n, e) {
        return e >= n.length - 1 ? n.pop() : n.splice(e, 1)[0];
      }
      function Ns(n, e) {
        const t = [];
        for (let i = 0; i < n; i++) t.push(e);
        return t;
      }
      function xt(n, e, t) {
        let i = Dr(n, e);
        return (
          i >= 0
            ? (n[1 | i] = t)
            : ((i = ~i),
              (function VS(n, e, t, i) {
                let r = n.length;
                if (r == e) n.push(t, i);
                else if (1 === r) n.push(i, n[0]), (n[0] = t);
                else {
                  for (r--, n.push(n[r - 1], n[r]); r > e; )
                    (n[r] = n[r - 2]), r--;
                  (n[e] = t), (n[e + 1] = i);
                }
              })(n, i, e, t)),
          i
        );
      }
      function yu(n, e) {
        const t = Dr(n, e);
        if (t >= 0) return n[1 | t];
      }
      function Dr(n, e) {
        return (function Wg(n, e, t) {
          let i = 0,
            r = n.length >> t;
          for (; r !== i; ) {
            const s = i + ((r - i) >> 1),
              o = n[s << t];
            if (e === o) return s << t;
            o > e ? (r = s) : (i = s + 1);
          }
          return ~(r << t);
        })(n, e, 1);
      }
      const Ls = {},
        bu = "__NG_DI_FLAG__",
        Ma = "ngTempTokenPath",
        GS = /\n/gm,
        Yg = "__source",
        WS = me({ provide: String, useValue: me });
      let Vs;
      function Zg(n) {
        const e = Vs;
        return (Vs = n), e;
      }
      function KS(n, e = U.Default) {
        if (void 0 === Vs) throw new ne(203, "");
        return null === Vs
          ? og(n, void 0, e)
          : Vs.get(n, e & U.Optional ? null : void 0, e);
      }
      function b(n, e = U.Default) {
        return (
          (function P0() {
            return Gc;
          })() || KS
        )(z(n), e);
      }
      const Xg = b;
      function Cu(n) {
        const e = [];
        for (let t = 0; t < n.length; t++) {
          const i = z(n[t]);
          if (Array.isArray(i)) {
            if (0 === i.length) throw new ne(900, "");
            let r,
              s = U.Default;
            for (let o = 0; o < i.length; o++) {
              const a = i[o],
                l = YS(a);
              "number" == typeof l
                ? -1 === l
                  ? (r = a.token)
                  : (s |= l)
                : (r = a);
            }
            e.push(b(r, s));
          } else e.push(b(i));
        }
        return e;
      }
      function Bs(n, e) {
        return (n[bu] = e), (n.prototype[bu] = e), n;
      }
      function YS(n) {
        return n[bu];
      }
      const js = Bs(
          wr("Inject", (n) => ({ token: n })),
          -1
        ),
        An = Bs(wr("Optional"), 8),
        Er = Bs(wr("SkipSelf"), 4);
      class om {
        constructor(e) {
          this.changingThisBreaksApplicationSecurity = e;
        }
        toString() {
          return `SafeValue must use [property]=binding: ${this.changingThisBreaksApplicationSecurity} (see https://g.co/ng/security#xss)`;
        }
      }
      function pi(n) {
        return n instanceof om ? n.changingThisBreaksApplicationSecurity : n;
      }
      const _A =
          /^(?:(?:https?|mailto|ftp|tel|file|sms):|[^&:/?#]*(?:[/?#]|$))/gi,
        yA =
          /^data:(?:image\/(?:bmp|gif|jpeg|jpg|png|tiff|webp)|video\/(?:mpeg|mp4|ogg|webm)|audio\/(?:mp3|oga|ogg|opus));base64,[a-z0-9+\/]+=*$/i;
      var Ue = (() => (
        ((Ue = Ue || {})[(Ue.NONE = 0)] = "NONE"),
        (Ue[(Ue.HTML = 1)] = "HTML"),
        (Ue[(Ue.STYLE = 2)] = "STYLE"),
        (Ue[(Ue.SCRIPT = 3)] = "SCRIPT"),
        (Ue[(Ue.URL = 4)] = "URL"),
        (Ue[(Ue.RESOURCE_URL = 5)] = "RESOURCE_URL"),
        Ue
      ))();
      function Ar(n) {
        const e = (function zs() {
          const n = C();
          return n && n[12];
        })();
        return e
          ? e.sanitize(Ue.URL, n) || ""
          : (function Us(n, e) {
              const t = (function fA(n) {
                return (n instanceof om && n.getTypeName()) || null;
              })(n);
              if (null != t && t !== e) {
                if ("ResourceURL" === t && "URL" === e) return !0;
                throw new Error(
                  `Required a safe ${e}, got a ${t} (see https://g.co/ng/security#xss)`
                );
              }
              return t === e;
            })(n, "URL")
          ? pi(n)
          : (function Oa(n) {
              return (n = String(n)).match(_A) || n.match(yA)
                ? n
                : "unsafe:" + n;
            })(B(n));
      }
      const mm = "__ngContext__";
      function lt(n, e) {
        n[mm] = e;
      }
      function Iu(n) {
        const e = (function Gs(n) {
          return n[mm] || null;
        })(n);
        return e ? (Array.isArray(e) ? e : e.lView) : null;
      }
      function ku(n) {
        return n.ngOriginalError;
      }
      function HA(n, ...e) {
        n.error(...e);
      }
      class Tr {
        constructor() {
          this._console = console;
        }
        handleError(e) {
          const t = this._findOriginalError(e),
            i = (function jA(n) {
              return (n && n.ngErrorLogger) || HA;
            })(e);
          i(this._console, "ERROR", e),
            t && i(this._console, "ORIGINAL ERROR", t);
        }
        _findOriginalError(e) {
          let t = e && ku(e);
          for (; t && ku(t); ) t = ku(t);
          return t || null;
        }
      }
      const Cm = (() =>
        (
          ("undefined" != typeof requestAnimationFrame &&
            requestAnimationFrame) ||
          setTimeout
        ).bind(pe))();
      function On(n) {
        return n instanceof Function ? n() : n;
      }
      var kt = (() => (
        ((kt = kt || {})[(kt.Important = 1)] = "Important"),
        (kt[(kt.DashCase = 2)] = "DashCase"),
        kt
      ))();
      function Ru(n, e) {
        return undefined(n, e);
      }
      function qs(n) {
        const e = n[3];
        return cn(e) ? e[3] : e;
      }
      function Pu(n) {
        return Sm(n[13]);
      }
      function Nu(n) {
        return Sm(n[4]);
      }
      function Sm(n) {
        for (; null !== n && !cn(n); ) n = n[4];
        return n;
      }
      function Ir(n, e, t, i, r) {
        if (null != i) {
          let s,
            o = !1;
          cn(i) ? (s = i) : En(i) && ((o = !0), (i = i[0]));
          const a = He(i);
          0 === n && null !== t
            ? null == r
              ? km(e, t, a)
              : ji(e, t, a, r || null, !0)
            : 1 === n && null !== t
            ? ji(e, t, a, r || null, !0)
            : 2 === n
            ? (function Bm(n, e, t) {
                const i = xa(n, e);
                i &&
                  (function uT(n, e, t, i) {
                    Re(n) ? n.removeChild(e, t, i) : e.removeChild(t);
                  })(n, i, e, t);
              })(e, a, o)
            : 3 === n && e.destroyNode(a),
            null != s &&
              (function fT(n, e, t, i, r) {
                const s = t[7];
                s !== He(t) && Ir(e, n, i, s, r);
                for (let a = 10; a < t.length; a++) {
                  const l = t[a];
                  Ws(l[1], l, n, e, i, s);
                }
              })(e, n, s, t, r);
        }
      }
      function Vu(n, e, t) {
        return Re(n)
          ? n.createElement(e, t)
          : null === t
          ? n.createElement(e)
          : n.createElementNS(t, e);
      }
      function Tm(n, e) {
        const t = n[9],
          i = t.indexOf(e),
          r = e[3];
        1024 & e[2] && ((e[2] &= -1025), iu(r, -1)), t.splice(i, 1);
      }
      function Bu(n, e) {
        if (n.length <= 10) return;
        const t = 10 + e,
          i = n[t];
        if (i) {
          const r = i[17];
          null !== r && r !== n && Tm(r, i), e > 0 && (n[t - 1][4] = i[4]);
          const s = Da(n, 10 + e);
          !(function nT(n, e) {
            Ws(n, e, e[G], 2, null, null), (e[0] = null), (e[6] = null);
          })(i[1], i);
          const o = s[19];
          null !== o && o.detachView(s[1]),
            (i[3] = null),
            (i[4] = null),
            (i[2] &= -129);
        }
        return i;
      }
      function Om(n, e) {
        if (!(256 & e[2])) {
          const t = e[G];
          Re(t) && t.destroyNode && Ws(n, e, t, 3, null, null),
            (function sT(n) {
              let e = n[13];
              if (!e) return ju(n[1], n);
              for (; e; ) {
                let t = null;
                if (En(e)) t = e[13];
                else {
                  const i = e[10];
                  i && (t = i);
                }
                if (!t) {
                  for (; e && !e[4] && e !== n; )
                    En(e) && ju(e[1], e), (e = e[3]);
                  null === e && (e = n), En(e) && ju(e[1], e), (t = e && e[4]);
                }
                e = t;
              }
            })(e);
        }
      }
      function ju(n, e) {
        if (!(256 & e[2])) {
          (e[2] &= -129),
            (e[2] |= 256),
            (function cT(n, e) {
              let t;
              if (null != n && null != (t = n.destroyHooks))
                for (let i = 0; i < t.length; i += 2) {
                  const r = e[t[i]];
                  if (!(r instanceof Is)) {
                    const s = t[i + 1];
                    if (Array.isArray(s))
                      for (let o = 0; o < s.length; o += 2) {
                        const a = r[s[o]],
                          l = s[o + 1];
                        try {
                          l.call(a);
                        } finally {
                        }
                      }
                    else
                      try {
                        s.call(r);
                      } finally {
                      }
                  }
                }
            })(n, e),
            (function lT(n, e) {
              const t = n.cleanup,
                i = e[7];
              let r = -1;
              if (null !== t)
                for (let s = 0; s < t.length - 1; s += 2)
                  if ("string" == typeof t[s]) {
                    const o = t[s + 1],
                      a = "function" == typeof o ? o(e) : He(e[o]),
                      l = i[(r = t[s + 2])],
                      c = t[s + 3];
                    "boolean" == typeof c
                      ? a.removeEventListener(t[s], l, c)
                      : c >= 0
                      ? i[(r = c)]()
                      : i[(r = -c)].unsubscribe(),
                      (s += 2);
                  } else {
                    const o = i[(r = t[s + 1])];
                    t[s].call(o);
                  }
              if (null !== i) {
                for (let s = r + 1; s < i.length; s++) i[s]();
                e[7] = null;
              }
            })(n, e),
            1 === e[1].type && Re(e[G]) && e[G].destroy();
          const t = e[17];
          if (null !== t && cn(e[3])) {
            t !== e[3] && Tm(t, e);
            const i = e[19];
            null !== i && i.detachView(n);
          }
        }
      }
      function Im(n, e, t) {
        return (function xm(n, e, t) {
          let i = e;
          for (; null !== i && 40 & i.type; ) i = (e = i).parent;
          if (null === i) return t[0];
          if (2 & i.flags) {
            const r = n.data[i.directiveStart].encapsulation;
            if (r === an.None || r === an.Emulated) return null;
          }
          return Wt(i, t);
        })(n, e.parent, t);
      }
      function ji(n, e, t, i, r) {
        Re(n) ? n.insertBefore(e, t, i, r) : e.insertBefore(t, i, r);
      }
      function km(n, e, t) {
        Re(n) ? n.appendChild(e, t) : e.appendChild(t);
      }
      function Fm(n, e, t, i, r) {
        null !== i ? ji(n, e, t, i, r) : km(n, e, t);
      }
      function xa(n, e) {
        return Re(n) ? n.parentNode(e) : e.parentNode;
      }
      function Rm(n, e, t) {
        return Nm(n, e, t);
      }
      let Nm = function Pm(n, e, t) {
        return 40 & n.type ? Wt(n, t) : null;
      };
      function ka(n, e, t, i) {
        const r = Im(n, i, e),
          s = e[G],
          a = Rm(i.parent || e[6], i, e);
        if (null != r)
          if (Array.isArray(t))
            for (let l = 0; l < t.length; l++) Fm(s, r, t[l], a, !1);
          else Fm(s, r, t, a, !1);
      }
      function Fa(n, e) {
        if (null !== e) {
          const t = e.type;
          if (3 & t) return Wt(e, n);
          if (4 & t) return Uu(-1, n[e.index]);
          if (8 & t) {
            const i = e.child;
            if (null !== i) return Fa(n, i);
            {
              const r = n[e.index];
              return cn(r) ? Uu(-1, r) : He(r);
            }
          }
          if (32 & t) return Ru(e, n)() || He(n[e.index]);
          {
            const i = Vm(n, e);
            return null !== i
              ? Array.isArray(i)
                ? i[0]
                : Fa(qs(n[16]), i)
              : Fa(n, e.next);
          }
        }
        return null;
      }
      function Vm(n, e) {
        return null !== e ? n[16][6].projection[e.projection] : null;
      }
      function Uu(n, e) {
        const t = 10 + n + 1;
        if (t < e.length) {
          const i = e[t],
            r = i[1].firstChild;
          if (null !== r) return Fa(i, r);
        }
        return e[7];
      }
      function $u(n, e, t, i, r, s, o) {
        for (; null != t; ) {
          const a = i[t.index],
            l = t.type;
          if (
            (o && 0 === e && (a && lt(He(a), i), (t.flags |= 4)),
            64 != (64 & t.flags))
          )
            if (8 & l) $u(n, e, t.child, i, r, s, !1), Ir(e, n, r, a, s);
            else if (32 & l) {
              const c = Ru(t, i);
              let u;
              for (; (u = c()); ) Ir(e, n, r, u, s);
              Ir(e, n, r, a, s);
            } else 16 & l ? jm(n, e, i, t, r, s) : Ir(e, n, r, a, s);
          t = o ? t.projectionNext : t.next;
        }
      }
      function Ws(n, e, t, i, r, s) {
        $u(t, i, n.firstChild, e, r, s, !1);
      }
      function jm(n, e, t, i, r, s) {
        const o = t[16],
          l = o[6].projection[i.projection];
        if (Array.isArray(l))
          for (let c = 0; c < l.length; c++) Ir(e, n, r, l[c], s);
        else $u(n, e, l, o[3], r, s, !0);
      }
      function Hm(n, e, t) {
        Re(n) ? n.setAttribute(e, "style", t) : (e.style.cssText = t);
      }
      function zu(n, e, t) {
        Re(n)
          ? "" === t
            ? n.removeAttribute(e, "class")
            : n.setAttribute(e, "class", t)
          : (e.className = t);
      }
      function Um(n, e, t) {
        let i = n.length;
        for (;;) {
          const r = n.indexOf(e, t);
          if (-1 === r) return r;
          if (0 === r || n.charCodeAt(r - 1) <= 32) {
            const s = e.length;
            if (r + s === i || n.charCodeAt(r + s) <= 32) return r;
          }
          t = r + 1;
        }
      }
      const $m = "ng-template";
      function gT(n, e, t) {
        let i = 0;
        for (; i < n.length; ) {
          let r = n[i++];
          if (t && "class" === r) {
            if (((r = n[i]), -1 !== Um(r.toLowerCase(), e, 0))) return !0;
          } else if (1 === r) {
            for (; i < n.length && "string" == typeof (r = n[i++]); )
              if (r.toLowerCase() === e) return !0;
            return !1;
          }
        }
        return !1;
      }
      function zm(n) {
        return 4 === n.type && n.value !== $m;
      }
      function mT(n, e, t) {
        return e === (4 !== n.type || t ? n.value : $m);
      }
      function _T(n, e, t) {
        let i = 4;
        const r = n.attrs || [],
          s = (function bT(n) {
            for (let e = 0; e < n.length; e++) if (kg(n[e])) return e;
            return n.length;
          })(r);
        let o = !1;
        for (let a = 0; a < e.length; a++) {
          const l = e[a];
          if ("number" != typeof l) {
            if (!o)
              if (4 & i) {
                if (
                  ((i = 2 | (1 & i)),
                  ("" !== l && !mT(n, l, t)) || ("" === l && 1 === e.length))
                ) {
                  if (dn(i)) return !1;
                  o = !0;
                }
              } else {
                const c = 8 & i ? l : e[++a];
                if (8 & i && null !== n.attrs) {
                  if (!gT(n.attrs, c, t)) {
                    if (dn(i)) return !1;
                    o = !0;
                  }
                  continue;
                }
                const d = yT(8 & i ? "class" : l, r, zm(n), t);
                if (-1 === d) {
                  if (dn(i)) return !1;
                  o = !0;
                  continue;
                }
                if ("" !== c) {
                  let h;
                  h = d > s ? "" : r[d + 1].toLowerCase();
                  const f = 8 & i ? h : null;
                  if ((f && -1 !== Um(f, c, 0)) || (2 & i && c !== h)) {
                    if (dn(i)) return !1;
                    o = !0;
                  }
                }
              }
          } else {
            if (!o && !dn(i) && !dn(l)) return !1;
            if (o && dn(l)) continue;
            (o = !1), (i = l | (1 & i));
          }
        }
        return dn(i) || o;
      }
      function dn(n) {
        return 0 == (1 & n);
      }
      function yT(n, e, t, i) {
        if (null === e) return -1;
        let r = 0;
        if (i || !t) {
          let s = !1;
          for (; r < e.length; ) {
            const o = e[r];
            if (o === n) return r;
            if (3 === o || 6 === o) s = !0;
            else {
              if (1 === o || 2 === o) {
                let a = e[++r];
                for (; "string" == typeof a; ) a = e[++r];
                continue;
              }
              if (4 === o) break;
              if (0 === o) {
                r += 4;
                continue;
              }
            }
            r += s ? 1 : 2;
          }
          return -1;
        }
        return (function CT(n, e) {
          let t = n.indexOf(4);
          if (t > -1)
            for (t++; t < n.length; ) {
              const i = n[t];
              if ("number" == typeof i) return -1;
              if (i === e) return t;
              t++;
            }
          return -1;
        })(e, n);
      }
      function Gm(n, e, t = !1) {
        for (let i = 0; i < e.length; i++) if (_T(n, e[i], t)) return !0;
        return !1;
      }
      function wT(n, e) {
        e: for (let t = 0; t < e.length; t++) {
          const i = e[t];
          if (n.length === i.length) {
            for (let r = 0; r < n.length; r++) if (n[r] !== i[r]) continue e;
            return !0;
          }
        }
        return !1;
      }
      function qm(n, e) {
        return n ? ":not(" + e.trim() + ")" : e;
      }
      function DT(n) {
        let e = n[0],
          t = 1,
          i = 2,
          r = "",
          s = !1;
        for (; t < n.length; ) {
          let o = n[t];
          if ("string" == typeof o)
            if (2 & i) {
              const a = n[++t];
              r += "[" + o + (a.length > 0 ? '="' + a + '"' : "") + "]";
            } else 8 & i ? (r += "." + o) : 4 & i && (r += " " + o);
          else
            "" !== r && !dn(o) && ((e += qm(s, r)), (r = "")),
              (i = o),
              (s = s || !dn(i));
          t++;
        }
        return "" !== r && (e += qm(s, r)), e;
      }
      const j = {};
      function k(n) {
        Wm(ie(), C(), pt() + n, ua());
      }
      function Wm(n, e, t, i) {
        if (!i)
          if (3 == (3 & e[2])) {
            const s = n.preOrderCheckHooks;
            null !== s && ga(e, s, t);
          } else {
            const s = n.preOrderHooks;
            null !== s && ma(e, s, 0, t);
          }
        hi(t);
      }
      function Ra(n, e) {
        return (n << 17) | (e << 2);
      }
      function hn(n) {
        return (n >> 17) & 32767;
      }
      function Gu(n) {
        return 2 | n;
      }
      function Wn(n) {
        return (131068 & n) >> 2;
      }
      function qu(n, e) {
        return (-131069 & n) | (e << 2);
      }
      function Wu(n) {
        return 1 | n;
      }
      function r_(n, e) {
        const t = n.contentQueries;
        if (null !== t)
          for (let i = 0; i < t.length; i += 2) {
            const r = t[i],
              s = t[i + 1];
            if (-1 !== s) {
              const o = n.data[s];
              lu(r), o.contentQueries(2, e[s], s);
            }
          }
      }
      function Ks(n, e, t, i, r, s, o, a, l, c) {
        const u = e.blueprint.slice();
        return (
          (u[0] = r),
          (u[2] = 140 | i),
          bg(u),
          (u[3] = u[15] = n),
          (u[8] = t),
          (u[10] = o || (n && n[10])),
          (u[G] = a || (n && n[G])),
          (u[12] = l || (n && n[12]) || null),
          (u[9] = c || (n && n[9]) || null),
          (u[6] = s),
          (u[16] = 2 == e.type ? n[16] : u),
          u
        );
      }
      function xr(n, e, t, i, r) {
        let s = n.data[e];
        if (null === s)
          (s = (function nd(n, e, t, i, r) {
            const s = wg(),
              o = ru(),
              l = (n.data[e] = (function HT(n, e, t, i, r, s) {
                return {
                  type: t,
                  index: i,
                  insertBeforeIndex: null,
                  injectorIndex: e ? e.injectorIndex : -1,
                  directiveStart: -1,
                  directiveEnd: -1,
                  directiveStylingLast: -1,
                  propertyBindings: null,
                  flags: 0,
                  providerIndexes: 0,
                  value: r,
                  attrs: s,
                  mergedAttrs: null,
                  localNames: null,
                  initialInputs: void 0,
                  inputs: null,
                  outputs: null,
                  tViews: null,
                  next: null,
                  projectionNext: null,
                  child: null,
                  parent: e,
                  projection: null,
                  styles: null,
                  stylesWithoutHost: null,
                  residualStyles: void 0,
                  classes: null,
                  classesWithoutHost: null,
                  residualClasses: void 0,
                  classBindings: 0,
                  styleBindings: 0,
                };
              })(0, o ? s : s && s.parent, t, e, i, r));
            return (
              null === n.firstChild && (n.firstChild = l),
              null !== s &&
                (o
                  ? null == s.child && null !== l.parent && (s.child = l)
                  : null === s.next && (s.next = l)),
              l
            );
          })(n, e, t, i, r)),
            (function uS() {
              return V.lFrame.inI18n;
            })() && (s.flags |= 64);
        else if (64 & s.type) {
          (s.type = t), (s.value = i), (s.attrs = r);
          const o = (function Os() {
            const n = V.lFrame,
              e = n.currentTNode;
            return n.isParent ? e : e.parent;
          })();
          s.injectorIndex = null === o ? -1 : o.injectorIndex;
        }
        return Mn(s, !0), s;
      }
      function kr(n, e, t, i) {
        if (0 === t) return -1;
        const r = e.length;
        for (let s = 0; s < t; s++)
          e.push(i), n.blueprint.push(i), n.data.push(null);
        return r;
      }
      function Ys(n, e, t) {
        ha(e);
        try {
          const i = n.viewQuery;
          null !== i && dd(1, i, t);
          const r = n.template;
          null !== r && s_(n, e, r, 1, t),
            n.firstCreatePass && (n.firstCreatePass = !1),
            n.staticContentQueries && r_(n, e),
            n.staticViewQueries && dd(2, n.viewQuery, t);
          const s = n.components;
          null !== s &&
            (function VT(n, e) {
              for (let t = 0; t < e.length; t++) sO(n, e[t]);
            })(e, s);
        } catch (i) {
          throw (
            (n.firstCreatePass &&
              ((n.incompleteFirstPass = !0), (n.firstCreatePass = !1)),
            i)
          );
        } finally {
          (e[2] &= -5), fa();
        }
      }
      function Fr(n, e, t, i) {
        const r = e[2];
        if (256 == (256 & r)) return;
        ha(e);
        const s = ua();
        try {
          bg(e),
            (function Dg(n) {
              return (V.lFrame.bindingIndex = n);
            })(n.bindingStartIndex),
            null !== t && s_(n, e, t, 2, i);
          const o = 3 == (3 & r);
          if (!s)
            if (o) {
              const c = n.preOrderCheckHooks;
              null !== c && ga(e, c, null);
            } else {
              const c = n.preOrderHooks;
              null !== c && ma(e, c, 0, null), cu(e, 0);
            }
          if (
            ((function iO(n) {
              for (let e = Pu(n); null !== e; e = Nu(e)) {
                if (!e[2]) continue;
                const t = e[9];
                for (let i = 0; i < t.length; i++) {
                  const r = t[i],
                    s = r[3];
                  0 == (1024 & r[2]) && iu(s, 1), (r[2] |= 1024);
                }
              }
            })(e),
            (function nO(n) {
              for (let e = Pu(n); null !== e; e = Nu(e))
                for (let t = 10; t < e.length; t++) {
                  const i = e[t],
                    r = i[1];
                  nu(i) && Fr(r, i, r.template, i[8]);
                }
            })(e),
            null !== n.contentQueries && r_(n, e),
            !s)
          )
            if (o) {
              const c = n.contentCheckHooks;
              null !== c && ga(e, c);
            } else {
              const c = n.contentHooks;
              null !== c && ma(e, c, 1), cu(e, 1);
            }
          !(function NT(n, e) {
            const t = n.hostBindingOpCodes;
            if (null !== t)
              try {
                for (let i = 0; i < t.length; i++) {
                  const r = t[i];
                  if (r < 0) hi(~r);
                  else {
                    const s = r,
                      o = t[++i],
                      a = t[++i];
                    dS(o, s), a(2, e[s]);
                  }
                }
              } finally {
                hi(-1);
              }
          })(n, e);
          const a = n.components;
          null !== a &&
            (function LT(n, e) {
              for (let t = 0; t < e.length; t++) rO(n, e[t]);
            })(e, a);
          const l = n.viewQuery;
          if ((null !== l && dd(2, l, i), !s))
            if (o) {
              const c = n.viewCheckHooks;
              null !== c && ga(e, c);
            } else {
              const c = n.viewHooks;
              null !== c && ma(e, c, 2), cu(e, 2);
            }
          !0 === n.firstUpdatePass && (n.firstUpdatePass = !1),
            s || (e[2] &= -73),
            1024 & e[2] && ((e[2] &= -1025), iu(e[3], -1));
        } finally {
          fa();
        }
      }
      function BT(n, e, t, i) {
        const r = e[10],
          s = !ua(),
          o = vg(e);
        try {
          s && !o && r.begin && r.begin(), o && Ys(n, e, i), Fr(n, e, t, i);
        } finally {
          s && !o && r.end && r.end();
        }
      }
      function s_(n, e, t, i, r) {
        const s = pt(),
          o = 2 & i;
        try {
          hi(-1), o && e.length > 20 && Wm(n, e, 20, ua()), t(i, r);
        } finally {
          hi(s);
        }
      }
      function o_(n, e, t) {
        if (Zc(e)) {
          const r = e.directiveEnd;
          for (let s = e.directiveStart; s < r; s++) {
            const o = n.data[s];
            o.contentQueries && o.contentQueries(1, t[s], s);
          }
        }
      }
      function id(n, e, t) {
        !Cg() ||
          ((function KT(n, e, t, i) {
            const r = t.directiveStart,
              s = t.directiveEnd;
            n.firstCreatePass || ks(t, e), lt(i, e);
            const o = t.initialInputs;
            for (let a = r; a < s; a++) {
              const l = n.data[a],
                c = un(l);
              c && JT(e, t, l);
              const u = Fs(e, n, a, t);
              lt(u, e),
                null !== o && eO(0, a - r, u, l, 0, o),
                c && (It(t.index, e)[8] = u);
            }
          })(n, e, t, Wt(t, e)),
          128 == (128 & t.flags) &&
            (function YT(n, e, t) {
              const i = t.directiveStart,
                r = t.directiveEnd,
                o = t.index,
                a = (function hS() {
                  return V.lFrame.currentDirectiveIndex;
                })();
              try {
                hi(o);
                for (let l = i; l < r; l++) {
                  const c = n.data[l],
                    u = e[l];
                  ou(l),
                    (null !== c.hostBindings ||
                      0 !== c.hostVars ||
                      null !== c.hostAttrs) &&
                      p_(c, u);
                }
              } finally {
                hi(-1), ou(a);
              }
            })(n, e, t));
      }
      function rd(n, e, t = Wt) {
        const i = e.localNames;
        if (null !== i) {
          let r = e.index + 1;
          for (let s = 0; s < i.length; s += 2) {
            const o = i[s + 1],
              a = -1 === o ? t(e, n) : n[o];
            n[r++] = a;
          }
        }
      }
      function a_(n) {
        const e = n.tView;
        return null === e || e.incompleteFirstPass
          ? (n.tView = La(
              1,
              null,
              n.template,
              n.decls,
              n.vars,
              n.directiveDefs,
              n.pipeDefs,
              n.viewQuery,
              n.schemas,
              n.consts
            ))
          : e;
      }
      function La(n, e, t, i, r, s, o, a, l, c) {
        const u = 20 + i,
          d = u + r,
          h = (function jT(n, e) {
            const t = [];
            for (let i = 0; i < e; i++) t.push(i < n ? null : j);
            return t;
          })(u, d),
          f = "function" == typeof c ? c() : c;
        return (h[1] = {
          type: n,
          blueprint: h,
          template: t,
          queries: null,
          viewQuery: a,
          declTNode: e,
          data: h.slice().fill(null, u),
          bindingStartIndex: u,
          expandoStartIndex: d,
          hostBindingOpCodes: null,
          firstCreatePass: !0,
          firstUpdatePass: !0,
          staticViewQueries: !1,
          staticContentQueries: !1,
          preOrderHooks: null,
          preOrderCheckHooks: null,
          contentHooks: null,
          contentCheckHooks: null,
          viewHooks: null,
          viewCheckHooks: null,
          destroyHooks: null,
          cleanup: null,
          contentQueries: null,
          components: null,
          directiveRegistry: "function" == typeof s ? s() : s,
          pipeRegistry: "function" == typeof o ? o() : o,
          firstChild: null,
          schemas: l,
          consts: f,
          incompleteFirstPass: !1,
        });
      }
      function u_(n, e, t, i) {
        const r = b_(e);
        null === t
          ? r.push(i)
          : (r.push(t), n.firstCreatePass && C_(n).push(i, r.length - 1));
      }
      function d_(n, e, t) {
        for (let i in n)
          if (n.hasOwnProperty(i)) {
            const r = n[i];
            (t = null === t ? {} : t).hasOwnProperty(i)
              ? t[i].push(e, r)
              : (t[i] = [e, r]);
          }
        return t;
      }
      function Ft(n, e, t, i, r, s, o, a) {
        const l = Wt(e, t);
        let u,
          c = e.inputs;
        !a && null != c && (u = c[i])
          ? (E_(n, t, u, i, r),
            aa(e) &&
              (function zT(n, e) {
                const t = It(e, n);
                16 & t[2] || (t[2] |= 64);
              })(t, e.index))
          : 3 & e.type &&
            ((i = (function $T(n) {
              return "class" === n
                ? "className"
                : "for" === n
                ? "htmlFor"
                : "formaction" === n
                ? "formAction"
                : "innerHtml" === n
                ? "innerHTML"
                : "readonly" === n
                ? "readOnly"
                : "tabindex" === n
                ? "tabIndex"
                : n;
            })(i)),
            (r = null != o ? o(r, e.value || "", i) : r),
            Re(s)
              ? s.setProperty(l, i, r)
              : du(i) || (l.setProperty ? l.setProperty(i, r) : (l[i] = r)));
      }
      function sd(n, e, t, i) {
        let r = !1;
        if (Cg()) {
          const s = (function ZT(n, e, t) {
              const i = n.directiveRegistry;
              let r = null;
              if (i)
                for (let s = 0; s < i.length; s++) {
                  const o = i[s];
                  Gm(t, o.selectors, !1) &&
                    (r || (r = []),
                    Ca(ks(t, e), n, o.type),
                    un(o) ? (g_(n, t), r.unshift(o)) : r.push(o));
                }
              return r;
            })(n, e, t),
            o = null === i ? null : { "": -1 };
          if (null !== s) {
            (r = !0), m_(t, n.data.length, s.length);
            for (let u = 0; u < s.length; u++) {
              const d = s[u];
              d.providersResolver && d.providersResolver(d);
            }
            let a = !1,
              l = !1,
              c = kr(n, e, s.length, null);
            for (let u = 0; u < s.length; u++) {
              const d = s[u];
              (t.mergedAttrs = ya(t.mergedAttrs, d.hostAttrs)),
                __(n, t, e, c, d),
                XT(c, d, o),
                null !== d.contentQueries && (t.flags |= 8),
                (null !== d.hostBindings ||
                  null !== d.hostAttrs ||
                  0 !== d.hostVars) &&
                  (t.flags |= 128);
              const h = d.type.prototype;
              !a &&
                (h.ngOnChanges || h.ngOnInit || h.ngDoCheck) &&
                ((n.preOrderHooks || (n.preOrderHooks = [])).push(t.index),
                (a = !0)),
                !l &&
                  (h.ngOnChanges || h.ngDoCheck) &&
                  ((n.preOrderCheckHooks || (n.preOrderCheckHooks = [])).push(
                    t.index
                  ),
                  (l = !0)),
                c++;
            }
            !(function UT(n, e) {
              const i = e.directiveEnd,
                r = n.data,
                s = e.attrs,
                o = [];
              let a = null,
                l = null;
              for (let c = e.directiveStart; c < i; c++) {
                const u = r[c],
                  d = u.inputs,
                  h = null === s || zm(e) ? null : tO(d, s);
                o.push(h), (a = d_(d, c, a)), (l = d_(u.outputs, c, l));
              }
              null !== a &&
                (a.hasOwnProperty("class") && (e.flags |= 16),
                a.hasOwnProperty("style") && (e.flags |= 32)),
                (e.initialInputs = o),
                (e.inputs = a),
                (e.outputs = l);
            })(n, t);
          }
          o &&
            (function QT(n, e, t) {
              if (e) {
                const i = (n.localNames = []);
                for (let r = 0; r < e.length; r += 2) {
                  const s = t[e[r + 1]];
                  if (null == s)
                    throw new ne(
                      -301,
                      `Export of name '${e[r + 1]}' not found!`
                    );
                  i.push(e[r], s);
                }
              }
            })(t, i, o);
        }
        return (t.mergedAttrs = ya(t.mergedAttrs, t.attrs)), r;
      }
      function f_(n, e, t, i, r, s) {
        const o = s.hostBindings;
        if (o) {
          let a = n.hostBindingOpCodes;
          null === a && (a = n.hostBindingOpCodes = []);
          const l = ~e.index;
          (function WT(n) {
            let e = n.length;
            for (; e > 0; ) {
              const t = n[--e];
              if ("number" == typeof t && t < 0) return t;
            }
            return 0;
          })(a) != l && a.push(l),
            a.push(i, r, o);
        }
      }
      function p_(n, e) {
        null !== n.hostBindings && n.hostBindings(1, e);
      }
      function g_(n, e) {
        (e.flags |= 2), (n.components || (n.components = [])).push(e.index);
      }
      function XT(n, e, t) {
        if (t) {
          if (e.exportAs)
            for (let i = 0; i < e.exportAs.length; i++) t[e.exportAs[i]] = n;
          un(e) && (t[""] = n);
        }
      }
      function m_(n, e, t) {
        (n.flags |= 1),
          (n.directiveStart = e),
          (n.directiveEnd = e + t),
          (n.providerIndexes = e);
      }
      function __(n, e, t, i, r) {
        n.data[i] = r;
        const s = r.factory || (r.factory = Vi(r.type)),
          o = new Is(s, un(r), null);
        (n.blueprint[i] = o),
          (t[i] = o),
          f_(n, e, 0, i, kr(n, t, r.hostVars, j), r);
      }
      function JT(n, e, t) {
        const i = Wt(e, n),
          r = a_(t),
          s = n[10],
          o = Va(
            n,
            Ks(
              n,
              r,
              null,
              t.onPush ? 64 : 16,
              i,
              e,
              s,
              s.createRenderer(i, t),
              null,
              null
            )
          );
        n[e.index] = o;
      }
      function In(n, e, t, i, r, s) {
        const o = Wt(n, e);
        !(function od(n, e, t, i, r, s, o) {
          if (null == s)
            Re(n) ? n.removeAttribute(e, r, t) : e.removeAttribute(r);
          else {
            const a = null == o ? B(s) : o(s, i || "", r);
            Re(n)
              ? n.setAttribute(e, r, a, t)
              : t
              ? e.setAttributeNS(t, r, a)
              : e.setAttribute(r, a);
          }
        })(e[G], o, s, n.value, t, i, r);
      }
      function eO(n, e, t, i, r, s) {
        const o = s[e];
        if (null !== o) {
          const a = i.setInput;
          for (let l = 0; l < o.length; ) {
            const c = o[l++],
              u = o[l++],
              d = o[l++];
            null !== a ? i.setInput(t, d, c, u) : (t[u] = d);
          }
        }
      }
      function tO(n, e) {
        let t = null,
          i = 0;
        for (; i < e.length; ) {
          const r = e[i];
          if (0 !== r)
            if (5 !== r) {
              if ("number" == typeof r) break;
              n.hasOwnProperty(r) &&
                (null === t && (t = []), t.push(r, n[r], e[i + 1])),
                (i += 2);
            } else i += 2;
          else i += 4;
        }
        return t;
      }
      function y_(n, e, t, i) {
        return new Array(n, !0, !1, e, null, 0, i, t, null, null);
      }
      function rO(n, e) {
        const t = It(e, n);
        if (nu(t)) {
          const i = t[1];
          80 & t[2] ? Fr(i, t, i.template, t[8]) : t[5] > 0 && ad(t);
        }
      }
      function ad(n) {
        for (let i = Pu(n); null !== i; i = Nu(i))
          for (let r = 10; r < i.length; r++) {
            const s = i[r];
            if (1024 & s[2]) {
              const o = s[1];
              Fr(o, s, o.template, s[8]);
            } else s[5] > 0 && ad(s);
          }
        const t = n[1].components;
        if (null !== t)
          for (let i = 0; i < t.length; i++) {
            const r = It(t[i], n);
            nu(r) && r[5] > 0 && ad(r);
          }
      }
      function sO(n, e) {
        const t = It(e, n),
          i = t[1];
        (function oO(n, e) {
          for (let t = e.length; t < n.blueprint.length; t++)
            e.push(n.blueprint[t]);
        })(i, t),
          Ys(i, t, t[8]);
      }
      function Va(n, e) {
        return n[13] ? (n[14][4] = e) : (n[13] = e), (n[14] = e), e;
      }
      function ld(n) {
        for (; n; ) {
          n[2] |= 64;
          const e = qs(n);
          if (G0(n) && !e) return n;
          n = e;
        }
        return null;
      }
      function ud(n, e, t) {
        const i = e[10];
        i.begin && i.begin();
        try {
          Fr(n, e, n.template, t);
        } catch (r) {
          throw (D_(e, r), r);
        } finally {
          i.end && i.end();
        }
      }
      function v_(n) {
        !(function cd(n) {
          for (let e = 0; e < n.components.length; e++) {
            const t = n.components[e],
              i = Iu(t),
              r = i[1];
            BT(r, i, r.template, t);
          }
        })(n[8]);
      }
      function dd(n, e, t) {
        lu(0), e(n, t);
      }
      const uO = (() => Promise.resolve(null))();
      function b_(n) {
        return n[7] || (n[7] = []);
      }
      function C_(n) {
        return n.cleanup || (n.cleanup = []);
      }
      function D_(n, e) {
        const t = n[9],
          i = t ? t.get(Tr, null) : null;
        i && i.handleError(e);
      }
      function E_(n, e, t, i, r) {
        for (let s = 0; s < t.length; ) {
          const o = t[s++],
            a = t[s++],
            l = e[o],
            c = n.data[o];
          null !== c.setInput ? c.setInput(l, r, i, a) : (l[a] = r);
        }
      }
      function Kn(n, e, t) {
        const i = ca(e, n);
        !(function Am(n, e, t) {
          Re(n) ? n.setValue(e, t) : (e.textContent = t);
        })(n[G], i, t);
      }
      function Ba(n, e, t) {
        let i = t ? n.styles : null,
          r = t ? n.classes : null,
          s = 0;
        if (null !== e)
          for (let o = 0; o < e.length; o++) {
            const a = e[o];
            "number" == typeof a
              ? (s = a)
              : 1 == s
              ? (r = Hc(r, a))
              : 2 == s && (i = Hc(i, a + ": " + e[++o] + ";"));
          }
        t ? (n.styles = i) : (n.stylesWithoutHost = i),
          t ? (n.classes = r) : (n.classesWithoutHost = r);
      }
      const hd = new T("INJECTOR", -1);
      class M_ {
        get(e, t = Ls) {
          if (t === Ls) {
            const i = new Error(`NullInjectorError: No provider for ${de(e)}!`);
            throw ((i.name = "NullInjectorError"), i);
          }
          return t;
        }
      }
      const fd = new T("Set Injector scope."),
        Zs = {},
        fO = {};
      let pd;
      function S_() {
        return void 0 === pd && (pd = new M_()), pd;
      }
      function A_(n, e = null, t = null, i) {
        const r = T_(n, e, t, i);
        return r._resolveInjectorDefTypes(), r;
      }
      function T_(n, e = null, t = null, i) {
        return new pO(n, t, e || S_(), i);
      }
      class pO {
        constructor(e, t, i, r = null) {
          (this.parent = i),
            (this.records = new Map()),
            (this.injectorDefTypes = new Set()),
            (this.onDestroy = new Set()),
            (this._destroyed = !1);
          const s = [];
          t && Sn(t, (a) => this.processProvider(a, e, t)),
            Sn([e], (a) => this.processInjectorType(a, [], s)),
            this.records.set(hd, Rr(void 0, this));
          const o = this.records.get(fd);
          (this.scope = null != o ? o.value : null),
            (this.source = r || ("object" == typeof e ? null : de(e)));
        }
        get destroyed() {
          return this._destroyed;
        }
        destroy() {
          this.assertNotDestroyed(), (this._destroyed = !0);
          try {
            this.onDestroy.forEach((e) => e.ngOnDestroy());
          } finally {
            this.records.clear(),
              this.onDestroy.clear(),
              this.injectorDefTypes.clear();
          }
        }
        get(e, t = Ls, i = U.Default) {
          this.assertNotDestroyed();
          const r = Zg(this),
            s = li(void 0);
          try {
            if (!(i & U.SkipSelf)) {
              let a = this.records.get(e);
              if (void 0 === a) {
                const l =
                  (function wO(n) {
                    return (
                      "function" == typeof n ||
                      ("object" == typeof n && n instanceof T)
                    );
                  })(e) && $c(e);
                (a = l && this.injectableDefInScope(l) ? Rr(gd(e), Zs) : null),
                  this.records.set(e, a);
              }
              if (null != a) return this.hydrate(e, a);
            }
            return (i & U.Self ? S_() : this.parent).get(
              e,
              (t = i & U.Optional && t === Ls ? null : t)
            );
          } catch (o) {
            if ("NullInjectorError" === o.name) {
              if (((o[Ma] = o[Ma] || []).unshift(de(e)), r)) throw o;
              return (function ZS(n, e, t, i) {
                const r = n[Ma];
                throw (
                  (e[Yg] && r.unshift(e[Yg]),
                  (n.message = (function QS(n, e, t, i = null) {
                    n =
                      n && "\n" === n.charAt(0) && "\u0275" == n.charAt(1)
                        ? n.substr(2)
                        : n;
                    let r = de(e);
                    if (Array.isArray(e)) r = e.map(de).join(" -> ");
                    else if ("object" == typeof e) {
                      let s = [];
                      for (let o in e)
                        if (e.hasOwnProperty(o)) {
                          let a = e[o];
                          s.push(
                            o +
                              ":" +
                              ("string" == typeof a ? JSON.stringify(a) : de(a))
                          );
                        }
                      r = `{${s.join(", ")}}`;
                    }
                    return `${t}${i ? "(" + i + ")" : ""}[${r}]: ${n.replace(
                      GS,
                      "\n  "
                    )}`;
                  })("\n" + n.message, r, t, i)),
                  (n.ngTokenPath = r),
                  (n[Ma] = null),
                  n)
                );
              })(o, e, "R3InjectorError", this.source);
            }
            throw o;
          } finally {
            li(s), Zg(r);
          }
        }
        _resolveInjectorDefTypes() {
          this.injectorDefTypes.forEach((e) => this.get(e));
        }
        toString() {
          const e = [];
          return (
            this.records.forEach((i, r) => e.push(de(r))),
            `R3Injector[${e.join(", ")}]`
          );
        }
        assertNotDestroyed() {
          if (this._destroyed) throw new ne(205, "");
        }
        processInjectorType(e, t, i) {
          if (!(e = z(e))) return !1;
          let r = rg(e);
          const s = (null == r && e.ngModule) || void 0,
            o = void 0 === s ? e : s,
            a = -1 !== i.indexOf(o);
          if ((void 0 !== s && (r = rg(s)), null == r)) return !1;
          if (null != r.imports && !a) {
            let u;
            i.push(o);
            try {
              Sn(r.imports, (d) => {
                this.processInjectorType(d, t, i) &&
                  (void 0 === u && (u = []), u.push(d));
              });
            } finally {
            }
            if (void 0 !== u)
              for (let d = 0; d < u.length; d++) {
                const { ngModule: h, providers: f } = u[d];
                Sn(f, (p) => this.processProvider(p, h, f || ye));
              }
          }
          this.injectorDefTypes.add(o);
          const l = Vi(o) || (() => new o());
          this.records.set(o, Rr(l, Zs));
          const c = r.providers;
          if (null != c && !a) {
            const u = e;
            Sn(c, (d) => this.processProvider(d, u, c));
          }
          return void 0 !== s && void 0 !== e.providers;
        }
        processProvider(e, t, i) {
          let r = Pr((e = z(e))) ? e : z(e && e.provide);
          const s = (function mO(n, e, t) {
            return I_(n) ? Rr(void 0, n.useValue) : Rr(O_(n), Zs);
          })(e);
          if (Pr(e) || !0 !== e.multi) this.records.get(r);
          else {
            let o = this.records.get(r);
            o ||
              ((o = Rr(void 0, Zs, !0)),
              (o.factory = () => Cu(o.multi)),
              this.records.set(r, o)),
              (r = e),
              o.multi.push(e);
          }
          this.records.set(r, s);
        }
        hydrate(e, t) {
          return (
            t.value === Zs && ((t.value = fO), (t.value = t.factory())),
            "object" == typeof t.value &&
              t.value &&
              (function CO(n) {
                return (
                  null !== n &&
                  "object" == typeof n &&
                  "function" == typeof n.ngOnDestroy
                );
              })(t.value) &&
              this.onDestroy.add(t.value),
            t.value
          );
        }
        injectableDefInScope(e) {
          if (!e.providedIn) return !1;
          const t = z(e.providedIn);
          return "string" == typeof t
            ? "any" === t || t === this.scope
            : this.injectorDefTypes.has(t);
        }
      }
      function gd(n) {
        const e = $c(n),
          t = null !== e ? e.factory : Vi(n);
        if (null !== t) return t;
        if (n instanceof T) throw new ne(204, "");
        if (n instanceof Function)
          return (function gO(n) {
            const e = n.length;
            if (e > 0) throw (Ns(e, "?"), new ne(204, ""));
            const t = (function k0(n) {
              const e = n && (n[na] || n[sg]);
              if (e) {
                const t = (function F0(n) {
                  if (n.hasOwnProperty("name")) return n.name;
                  const e = ("" + n).match(/^function\s*([^\s(]+)/);
                  return null === e ? "" : e[1];
                })(n);
                return (
                  console.warn(
                    `DEPRECATED: DI is instantiating a token "${t}" that inherits its @Injectable decorator but does not provide one itself.\nThis will become an error in a future version of Angular. Please add @Injectable() to the "${t}" class.`
                  ),
                  e
                );
              }
              return null;
            })(n);
            return null !== t ? () => t.factory(n) : () => new n();
          })(n);
        throw new ne(204, "");
      }
      function O_(n, e, t) {
        let i;
        if (Pr(n)) {
          const r = z(n);
          return Vi(r) || gd(r);
        }
        if (I_(n)) i = () => z(n.useValue);
        else if (
          (function yO(n) {
            return !(!n || !n.useFactory);
          })(n)
        )
          i = () => n.useFactory(...Cu(n.deps || []));
        else if (
          (function _O(n) {
            return !(!n || !n.useExisting);
          })(n)
        )
          i = () => b(z(n.useExisting));
        else {
          const r = z(n && (n.useClass || n.provide));
          if (
            !(function bO(n) {
              return !!n.deps;
            })(n)
          )
            return Vi(r) || gd(r);
          i = () => new r(...Cu(n.deps));
        }
        return i;
      }
      function Rr(n, e, t = !1) {
        return { factory: n, value: e, multi: t ? [] : void 0 };
      }
      function I_(n) {
        return null !== n && "object" == typeof n && WS in n;
      }
      function Pr(n) {
        return "function" == typeof n;
      }
      let Qe = (() => {
        class n {
          static create(t, i) {
            var r;
            if (Array.isArray(t)) return A_({ name: "" }, i, t, "");
            {
              const s = null !== (r = t.name) && void 0 !== r ? r : "";
              return A_({ name: s }, t.parent, t.providers, s);
            }
          }
        }
        return (
          (n.THROW_IF_NOT_FOUND = Ls),
          (n.NULL = new M_()),
          (n.ɵprov = I({ token: n, providedIn: "any", factory: () => b(hd) })),
          (n.__NG_ELEMENT_ID__ = -1),
          n
        );
      })();
      function IO(n, e) {
        pa(Iu(n)[1], Ye());
      }
      function se(n) {
        let e = (function U_(n) {
            return Object.getPrototypeOf(n.prototype).constructor;
          })(n.type),
          t = !0;
        const i = [n];
        for (; e; ) {
          let r;
          if (un(n)) r = e.ɵcmp || e.ɵdir;
          else {
            if (e.ɵcmp) throw new ne(903, "");
            r = e.ɵdir;
          }
          if (r) {
            if (t) {
              i.push(r);
              const o = n;
              (o.inputs = yd(n.inputs)),
                (o.declaredInputs = yd(n.declaredInputs)),
                (o.outputs = yd(n.outputs));
              const a = r.hostBindings;
              a && RO(n, a);
              const l = r.viewQuery,
                c = r.contentQueries;
              if (
                (l && kO(n, l),
                c && FO(n, c),
                jc(n.inputs, r.inputs),
                jc(n.declaredInputs, r.declaredInputs),
                jc(n.outputs, r.outputs),
                un(r) && r.data.animation)
              ) {
                const u = n.data;
                u.animation = (u.animation || []).concat(r.data.animation);
              }
            }
            const s = r.features;
            if (s)
              for (let o = 0; o < s.length; o++) {
                const a = s[o];
                a && a.ngInherit && a(n), a === se && (t = !1);
              }
          }
          e = Object.getPrototypeOf(e);
        }
        !(function xO(n) {
          let e = 0,
            t = null;
          for (let i = n.length - 1; i >= 0; i--) {
            const r = n[i];
            (r.hostVars = e += r.hostVars),
              (r.hostAttrs = ya(r.hostAttrs, (t = ya(t, r.hostAttrs))));
          }
        })(i);
      }
      function yd(n) {
        return n === cr ? {} : n === ye ? [] : n;
      }
      function kO(n, e) {
        const t = n.viewQuery;
        n.viewQuery = t
          ? (i, r) => {
              e(i, r), t(i, r);
            }
          : e;
      }
      function FO(n, e) {
        const t = n.contentQueries;
        n.contentQueries = t
          ? (i, r, s) => {
              e(i, r, s), t(i, r, s);
            }
          : e;
      }
      function RO(n, e) {
        const t = n.hostBindings;
        n.hostBindings = t
          ? (i, r) => {
              e(i, r), t(i, r);
            }
          : e;
      }
      let ja = null;
      function Nr() {
        if (!ja) {
          const n = pe.Symbol;
          if (n && n.iterator) ja = n.iterator;
          else {
            const e = Object.getOwnPropertyNames(Map.prototype);
            for (let t = 0; t < e.length; ++t) {
              const i = e[t];
              "entries" !== i &&
                "size" !== i &&
                Map.prototype[i] === Map.prototype.entries &&
                (ja = i);
            }
          }
        }
        return ja;
      }
      function Qs(n) {
        return (
          !!vd(n) && (Array.isArray(n) || (!(n instanceof Map) && Nr() in n))
        );
      }
      function vd(n) {
        return null !== n && ("function" == typeof n || "object" == typeof n);
      }
      function ct(n, e, t) {
        return !Object.is(n[e], t) && ((n[e] = t), !0);
      }
      function $e(n, e, t, i) {
        const r = C();
        return ct(r, gr(), e) && (ie(), In(Pe(), r, n, e, t, i)), $e;
      }
      function Vr(n, e, t, i) {
        return ct(n, gr(), t) ? e + B(t) + i : j;
      }
      function be(n, e, t, i, r, s, o, a) {
        const l = C(),
          c = ie(),
          u = n + 20,
          d = c.firstCreatePass
            ? (function HO(n, e, t, i, r, s, o, a, l) {
                const c = e.consts,
                  u = xr(e, n, 4, o || null, di(c, a));
                sd(e, t, u, di(c, l)), pa(e, u);
                const d = (u.tViews = La(
                  2,
                  u,
                  i,
                  r,
                  s,
                  e.directiveRegistry,
                  e.pipeRegistry,
                  null,
                  e.schemas,
                  c
                ));
                return (
                  null !== e.queries &&
                    (e.queries.template(e, u),
                    (d.queries = e.queries.embeddedTView(u))),
                  u
                );
              })(u, c, l, e, t, i, r, s, o)
            : c.data[u];
        Mn(d, !1);
        const h = l[G].createComment("");
        ka(c, l, h, d),
          lt(h, l),
          Va(l, (l[u] = y_(h, l, h, d))),
          la(d) && id(c, l, d),
          null != o && rd(l, d, a);
      }
      function bd(n) {
        return (function pr(n, e) {
          return n[e];
        })(
          (function cS() {
            return V.lFrame.contextLView;
          })(),
          20 + n
        );
      }
      function _(n, e = U.Default) {
        const t = C();
        return null === t ? b(n, e) : Bg(Ye(), t, z(n), e);
      }
      function $a() {
        throw new Error("invalid");
      }
      function F(n, e, t) {
        const i = C();
        return ct(i, gr(), e) && Ft(ie(), Pe(), i, n, e, i[G], t, !1), F;
      }
      function Md(n, e, t, i, r) {
        const o = r ? "class" : "style";
        E_(n, t, e.inputs[o], o, i);
      }
      function D(n, e, t, i) {
        const r = C(),
          s = ie(),
          o = 20 + n,
          a = r[G],
          l = (r[o] = Vu(
            a,
            e,
            (function bS() {
              return V.lFrame.currentNamespace;
            })()
          )),
          c = s.firstCreatePass
            ? (function lI(n, e, t, i, r, s, o) {
                const a = e.consts,
                  c = xr(e, n, 2, r, di(a, s));
                return (
                  sd(e, t, c, di(a, o)),
                  null !== c.attrs && Ba(c, c.attrs, !1),
                  null !== c.mergedAttrs && Ba(c, c.mergedAttrs, !0),
                  null !== e.queries && e.queries.elementStart(e, c),
                  c
                );
              })(o, s, r, 0, e, t, i)
            : s.data[o];
        Mn(c, !0);
        const u = c.mergedAttrs;
        null !== u && _a(a, l, u);
        const d = c.classes;
        null !== d && zu(a, l, d);
        const h = c.styles;
        null !== h && Hm(a, l, h),
          64 != (64 & c.flags) && ka(s, r, l, c),
          0 ===
            (function rS() {
              return V.lFrame.elementDepthCount;
            })() && lt(l, r),
          (function sS() {
            V.lFrame.elementDepthCount++;
          })(),
          la(c) && (id(s, r, c), o_(s, c, r)),
          null !== i && rd(r, c);
      }
      function E() {
        let n = Ye();
        ru() ? su() : ((n = n.parent), Mn(n, !1));
        const e = n;
        !(function oS() {
          V.lFrame.elementDepthCount--;
        })();
        const t = ie();
        t.firstCreatePass && (pa(t, n), Zc(n) && t.queries.elementEnd(n)),
          null != e.classesWithoutHost &&
            (function MS(n) {
              return 0 != (16 & n.flags);
            })(e) &&
            Md(t, e, C(), e.classesWithoutHost, !0),
          null != e.stylesWithoutHost &&
            (function SS(n) {
              return 0 != (32 & n.flags);
            })(e) &&
            Md(t, e, C(), e.stylesWithoutHost, !1);
      }
      function Me(n, e, t, i) {
        D(n, e, t, i), E();
      }
      function za(n, e, t) {
        const i = C(),
          r = ie(),
          s = n + 20,
          o = r.firstCreatePass
            ? (function cI(n, e, t, i, r) {
                const s = e.consts,
                  o = di(s, i),
                  a = xr(e, n, 8, "ng-container", o);
                return (
                  null !== o && Ba(a, o, !0),
                  sd(e, t, a, di(s, r)),
                  null !== e.queries && e.queries.elementStart(e, a),
                  a
                );
              })(s, r, i, e, t)
            : r.data[s];
        Mn(o, !0);
        const a = (i[s] = i[G].createComment(""));
        ka(r, i, a, o),
          lt(a, i),
          la(o) && (id(r, i, o), o_(r, o, i)),
          null != t && rd(i, o);
      }
      function Ga() {
        let n = Ye();
        const e = ie();
        ru() ? su() : ((n = n.parent), Mn(n, !1)),
          e.firstCreatePass && (pa(e, n), Zc(n) && e.queries.elementEnd(n));
      }
      function _i() {
        return C();
      }
      function Js(n) {
        return !!n && "function" == typeof n.then;
      }
      const Sd = function ly(n) {
        return !!n && "function" == typeof n.subscribe;
      };
      function Z(n, e, t, i) {
        const r = C(),
          s = ie(),
          o = Ye();
        return (
          (function uy(n, e, t, i, r, s, o, a) {
            const l = la(i),
              u = n.firstCreatePass && C_(n),
              d = e[8],
              h = b_(e);
            let f = !0;
            if (3 & i.type || a) {
              const y = Wt(i, e),
                v = a ? a(y) : y,
                m = h.length,
                w = a ? (A) => a(He(A[i.index])) : i.index;
              if (Re(t)) {
                let A = null;
                if (
                  (!a &&
                    l &&
                    (A = (function dI(n, e, t, i) {
                      const r = n.cleanup;
                      if (null != r)
                        for (let s = 0; s < r.length - 1; s += 2) {
                          const o = r[s];
                          if (o === t && r[s + 1] === i) {
                            const a = e[7],
                              l = r[s + 2];
                            return a.length > l ? a[l] : null;
                          }
                          "string" == typeof o && (s += 2);
                        }
                      return null;
                    })(n, e, r, i.index)),
                  null !== A)
                )
                  ((A.__ngLastListenerFn__ || A).__ngNextListenerFn__ = s),
                    (A.__ngLastListenerFn__ = s),
                    (f = !1);
                else {
                  s = Ad(i, e, d, s, !1);
                  const $ = t.listen(v, r, s);
                  h.push(s, $), u && u.push(r, w, m, m + 1);
                }
              } else
                (s = Ad(i, e, d, s, !0)),
                  v.addEventListener(r, s, o),
                  h.push(s),
                  u && u.push(r, w, m, o);
            } else s = Ad(i, e, d, s, !1);
            const p = i.outputs;
            let g;
            if (f && null !== p && (g = p[r])) {
              const y = g.length;
              if (y)
                for (let v = 0; v < y; v += 2) {
                  const Ae = e[g[v]][g[v + 1]].subscribe(s),
                    xe = h.length;
                  h.push(s, Ae), u && u.push(r, i.index, xe, -(xe + 1));
                }
            }
          })(s, r, r[G], o, n, e, !!t, i),
          Z
        );
      }
      function dy(n, e, t, i) {
        try {
          return !1 !== t(i);
        } catch (r) {
          return D_(n, r), !1;
        }
      }
      function Ad(n, e, t, i, r) {
        return function s(o) {
          if (o === Function) return i;
          const a = 2 & n.flags ? It(n.index, e) : e;
          0 == (32 & e[2]) && ld(a);
          let l = dy(e, 0, i, o),
            c = s.__ngNextListenerFn__;
          for (; c; ) (l = dy(e, 0, c, o) && l), (c = c.__ngNextListenerFn__);
          return r && !1 === l && (o.preventDefault(), (o.returnValue = !1)), l;
        };
      }
      function K(n = 1) {
        return (function pS(n) {
          return (V.lFrame.contextLView = (function gS(n, e) {
            for (; n > 0; ) (e = e[15]), n--;
            return e;
          })(n, V.lFrame.contextLView))[8];
        })(n);
      }
      function hI(n, e) {
        let t = null;
        const i = (function vT(n) {
          const e = n.attrs;
          if (null != e) {
            const t = e.indexOf(5);
            if (0 == (1 & t)) return e[t + 1];
          }
          return null;
        })(n);
        for (let r = 0; r < e.length; r++) {
          const s = e[r];
          if ("*" !== s) {
            if (null === i ? Gm(n, s, !0) : wT(i, s)) return r;
          } else t = r;
        }
        return t;
      }
      function eo(n) {
        const e = C()[16][6];
        if (!e.projection) {
          const i = (e.projection = Ns(n ? n.length : 1, null)),
            r = i.slice();
          let s = e.child;
          for (; null !== s; ) {
            const o = n ? hI(s, n) : 0;
            null !== o &&
              (r[o] ? (r[o].projectionNext = s) : (i[o] = s), (r[o] = s)),
              (s = s.next);
          }
        }
      }
      function Rt(n, e = 0, t) {
        const i = C(),
          r = ie(),
          s = xr(r, 20 + n, 16, null, t || null);
        null === s.projection && (s.projection = e),
          su(),
          64 != (64 & s.flags) &&
            (function hT(n, e, t) {
              jm(e[G], 0, e, t, Im(n, t, e), Rm(t.parent || e[6], t, e));
            })(r, i, s);
      }
      function Cy(n, e, t, i, r) {
        const s = n[t + 1],
          o = null === e;
        let a = i ? hn(s) : Wn(s),
          l = !1;
        for (; 0 !== a && (!1 === l || o); ) {
          const u = n[a + 1];
          gI(n[a], e) && ((l = !0), (n[a + 1] = i ? Wu(u) : Gu(u))),
            (a = i ? hn(u) : Wn(u));
        }
        l && (n[t + 1] = i ? Gu(s) : Wu(s));
      }
      function gI(n, e) {
        return (
          null === n ||
          null == e ||
          (Array.isArray(n) ? n[1] : n) === e ||
          (!(!Array.isArray(n) || "string" != typeof e) && Dr(n, e) >= 0)
        );
      }
      const Xe = { textEnd: 0, key: 0, keyEnd: 0, value: 0, valueEnd: 0 };
      function wy(n) {
        return n.substring(Xe.key, Xe.keyEnd);
      }
      function Dy(n, e) {
        const t = Xe.textEnd;
        return t === e
          ? -1
          : ((e = Xe.keyEnd =
              (function vI(n, e, t) {
                for (; e < t && n.charCodeAt(e) > 32; ) e++;
                return e;
              })(n, (Xe.key = e), t)),
            Wr(n, e, t));
      }
      function Wr(n, e, t) {
        for (; e < t && n.charCodeAt(e) <= 32; ) e++;
        return e;
      }
      function Od(n, e, t) {
        return pn(n, e, t, !1), Od;
      }
      function Dt(n, e) {
        return pn(n, e, null, !0), Dt;
      }
      function Fn(n, e) {
        for (
          let t = (function _I(n) {
            return (
              (function My(n) {
                (Xe.key = 0),
                  (Xe.keyEnd = 0),
                  (Xe.value = 0),
                  (Xe.valueEnd = 0),
                  (Xe.textEnd = n.length);
              })(n),
              Dy(n, Wr(n, 0, Xe.textEnd))
            );
          })(e);
          t >= 0;
          t = Dy(e, t)
        )
          xt(n, wy(e), !0);
      }
      function pn(n, e, t, i) {
        const r = C(),
          s = ie(),
          o = qn(2);
        s.firstUpdatePass && Oy(s, n, o, i),
          e !== j &&
            ct(r, o, e) &&
            xy(
              s,
              s.data[pt()],
              r,
              r[G],
              n,
              (r[o + 1] = (function II(n, e) {
                return (
                  null == n ||
                    ("string" == typeof e
                      ? (n += e)
                      : "object" == typeof n && (n = de(pi(n)))),
                  n
                );
              })(e, t)),
              i,
              o
            );
      }
      function Ty(n, e) {
        return e >= n.expandoStartIndex;
      }
      function Oy(n, e, t, i) {
        const r = n.data;
        if (null === r[t + 1]) {
          const s = r[pt()],
            o = Ty(n, t);
          Fy(s, i) && null === e && !o && (e = !1),
            (e = (function EI(n, e, t, i) {
              const r = (function au(n) {
                const e = V.lFrame.currentDirectiveIndex;
                return -1 === e ? null : n[e];
              })(n);
              let s = i ? e.residualClasses : e.residualStyles;
              if (null === r)
                0 === (i ? e.classBindings : e.styleBindings) &&
                  ((t = to((t = Id(null, n, e, t, i)), e.attrs, i)),
                  (s = null));
              else {
                const o = e.directiveStylingLast;
                if (-1 === o || n[o] !== r)
                  if (((t = Id(r, n, e, t, i)), null === s)) {
                    let l = (function MI(n, e, t) {
                      const i = t ? e.classBindings : e.styleBindings;
                      if (0 !== Wn(i)) return n[hn(i)];
                    })(n, e, i);
                    void 0 !== l &&
                      Array.isArray(l) &&
                      ((l = Id(null, n, e, l[1], i)),
                      (l = to(l, e.attrs, i)),
                      (function SI(n, e, t, i) {
                        n[hn(t ? e.classBindings : e.styleBindings)] = i;
                      })(n, e, i, l));
                  } else
                    s = (function AI(n, e, t) {
                      let i;
                      const r = e.directiveEnd;
                      for (let s = 1 + e.directiveStylingLast; s < r; s++)
                        i = to(i, n[s].hostAttrs, t);
                      return to(i, e.attrs, t);
                    })(n, e, i);
              }
              return (
                void 0 !== s &&
                  (i ? (e.residualClasses = s) : (e.residualStyles = s)),
                t
              );
            })(r, s, e, i)),
            (function fI(n, e, t, i, r, s) {
              let o = s ? e.classBindings : e.styleBindings,
                a = hn(o),
                l = Wn(o);
              n[i] = t;
              let u,
                c = !1;
              if (Array.isArray(t)) {
                const d = t;
                (u = d[1]), (null === u || Dr(d, u) > 0) && (c = !0);
              } else u = t;
              if (r)
                if (0 !== l) {
                  const h = hn(n[a + 1]);
                  (n[i + 1] = Ra(h, a)),
                    0 !== h && (n[h + 1] = qu(n[h + 1], i)),
                    (n[a + 1] = (function ST(n, e) {
                      return (131071 & n) | (e << 17);
                    })(n[a + 1], i));
                } else
                  (n[i + 1] = Ra(a, 0)),
                    0 !== a && (n[a + 1] = qu(n[a + 1], i)),
                    (a = i);
              else
                (n[i + 1] = Ra(l, 0)),
                  0 === a ? (a = i) : (n[l + 1] = qu(n[l + 1], i)),
                  (l = i);
              c && (n[i + 1] = Gu(n[i + 1])),
                Cy(n, u, i, !0),
                Cy(n, u, i, !1),
                (function pI(n, e, t, i, r) {
                  const s = r ? n.residualClasses : n.residualStyles;
                  null != s &&
                    "string" == typeof e &&
                    Dr(s, e) >= 0 &&
                    (t[i + 1] = Wu(t[i + 1]));
                })(e, u, n, i, s),
                (o = Ra(a, l)),
                s ? (e.classBindings = o) : (e.styleBindings = o);
            })(r, s, e, t, o, i);
        }
      }
      function Id(n, e, t, i, r) {
        let s = null;
        const o = t.directiveEnd;
        let a = t.directiveStylingLast;
        for (
          -1 === a ? (a = t.directiveStart) : a++;
          a < o && ((s = e[a]), (i = to(i, s.hostAttrs, r)), s !== n);

        )
          a++;
        return null !== n && (t.directiveStylingLast = a), i;
      }
      function to(n, e, t) {
        const i = t ? 1 : 2;
        let r = -1;
        if (null !== e)
          for (let s = 0; s < e.length; s++) {
            const o = e[s];
            "number" == typeof o
              ? (r = o)
              : r === i &&
                (Array.isArray(n) || (n = void 0 === n ? [] : ["", n]),
                xt(n, o, !!t || e[++s]));
          }
        return void 0 === n ? null : n;
      }
      function xy(n, e, t, i, r, s, o, a) {
        if (!(3 & e.type)) return;
        const l = n.data,
          c = l[a + 1];
        qa(
          (function Zm(n) {
            return 1 == (1 & n);
          })(c)
            ? ky(l, e, t, r, Wn(c), o)
            : void 0
        ) ||
          (qa(s) ||
            ((function Ym(n) {
              return 2 == (2 & n);
            })(c) &&
              (s = ky(l, null, t, r, a, o))),
          (function pT(n, e, t, i, r) {
            const s = Re(n);
            if (e)
              r
                ? s
                  ? n.addClass(t, i)
                  : t.classList.add(i)
                : s
                ? n.removeClass(t, i)
                : t.classList.remove(i);
            else {
              let o = -1 === i.indexOf("-") ? void 0 : kt.DashCase;
              if (null == r)
                s ? n.removeStyle(t, i, o) : t.style.removeProperty(i);
              else {
                const a = "string" == typeof r && r.endsWith("!important");
                a && ((r = r.slice(0, -10)), (o |= kt.Important)),
                  s
                    ? n.setStyle(t, i, r, o)
                    : t.style.setProperty(i, r, a ? "important" : "");
              }
            }
          })(i, o, ca(pt(), t), r, s));
      }
      function ky(n, e, t, i, r, s) {
        const o = null === e;
        let a;
        for (; r > 0; ) {
          const l = n[r],
            c = Array.isArray(l),
            u = c ? l[1] : l,
            d = null === u;
          let h = t[r + 1];
          h === j && (h = d ? ye : void 0);
          let f = d ? yu(h, i) : u === i ? h : void 0;
          if ((c && !qa(f) && (f = yu(l, i)), qa(f) && ((a = f), o))) return a;
          const p = n[r + 1];
          r = o ? hn(p) : Wn(p);
        }
        if (null !== e) {
          let l = s ? e.residualClasses : e.residualStyles;
          null != l && (a = yu(l, i));
        }
        return a;
      }
      function qa(n) {
        return void 0 !== n;
      }
      function Fy(n, e) {
        return 0 != (n.flags & (e ? 16 : 32));
      }
      function J(n, e = "") {
        const t = C(),
          i = ie(),
          r = n + 20,
          s = i.firstCreatePass ? xr(i, r, 1, e, null) : i.data[r],
          o = (t[r] = (function Lu(n, e) {
            return Re(n) ? n.createText(e) : n.createTextNode(e);
          })(t[G], e));
        ka(i, t, o, s), Mn(s, !1);
      }
      function Pt(n) {
        return no("", n, ""), Pt;
      }
      function no(n, e, t) {
        const i = C(),
          r = Vr(i, n, e, t);
        return r !== j && Kn(i, pt(), r), no;
      }
      function Uy(n, e, t) {
        !(function gn(n, e, t, i) {
          const r = ie(),
            s = qn(2);
          r.firstUpdatePass && Oy(r, null, s, i);
          const o = C();
          if (t !== j && ct(o, s, t)) {
            const a = r.data[pt()];
            if (Fy(a, i) && !Ty(r, s)) {
              let l = i ? a.classesWithoutHost : a.stylesWithoutHost;
              null !== l && (t = Hc(l, t || "")), Md(r, a, o, t, i);
            } else
              !(function OI(n, e, t, i, r, s, o, a) {
                r === j && (r = ye);
                let l = 0,
                  c = 0,
                  u = 0 < r.length ? r[0] : null,
                  d = 0 < s.length ? s[0] : null;
                for (; null !== u || null !== d; ) {
                  const h = l < r.length ? r[l + 1] : void 0,
                    f = c < s.length ? s[c + 1] : void 0;
                  let g,
                    p = null;
                  u === d
                    ? ((l += 2), (c += 2), h !== f && ((p = d), (g = f)))
                    : null === d || (null !== u && u < d)
                    ? ((l += 2), (p = u))
                    : ((c += 2), (p = d), (g = f)),
                    null !== p && xy(n, e, t, i, p, g, o, a),
                    (u = l < r.length ? r[l] : null),
                    (d = c < s.length ? s[c] : null);
                }
              })(
                r,
                a,
                o,
                o[G],
                o[s + 1],
                (o[s + 1] = (function TI(n, e, t) {
                  if (null == t || "" === t) return ye;
                  const i = [],
                    r = pi(t);
                  if (Array.isArray(r))
                    for (let s = 0; s < r.length; s++) n(i, r[s], !0);
                  else if ("object" == typeof r)
                    for (const s in r) r.hasOwnProperty(s) && n(i, s, r[s]);
                  else "string" == typeof r && e(i, r);
                  return i;
                })(n, e, t)),
                i,
                s
              );
          }
        })(xt, Fn, Vr(C(), n, e, t), !0);
      }
      function Wa(n, e, t) {
        const i = C();
        return ct(i, gr(), e) && Ft(ie(), Pe(), i, n, e, i[G], t, !0), Wa;
      }
      const Ui = void 0;
      var YI = [
        "en",
        [["a", "p"], ["AM", "PM"], Ui],
        [["AM", "PM"], Ui, Ui],
        [
          ["S", "M", "T", "W", "T", "F", "S"],
          ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
          [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
          ],
          ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"],
        ],
        Ui,
        [
          ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"],
          [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
          ],
          [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
          ],
        ],
        Ui,
        [
          ["B", "A"],
          ["BC", "AD"],
          ["Before Christ", "Anno Domini"],
        ],
        0,
        [6, 0],
        ["M/d/yy", "MMM d, y", "MMMM d, y", "EEEE, MMMM d, y"],
        ["h:mm a", "h:mm:ss a", "h:mm:ss a z", "h:mm:ss a zzzz"],
        ["{1}, {0}", Ui, "{1} 'at' {0}", Ui],
        [
          ".",
          ",",
          ";",
          "%",
          "+",
          "-",
          "E",
          "\xd7",
          "\u2030",
          "\u221e",
          "NaN",
          ":",
        ],
        ["#,##0.###", "#,##0%", "\xa4#,##0.00", "#E0"],
        "USD",
        "$",
        "US Dollar",
        {},
        "ltr",
        function KI(n) {
          const t = Math.floor(Math.abs(n)),
            i = n.toString().replace(/^[^.]*\.?/, "").length;
          return 1 === t && 0 === i ? 1 : 5;
        },
      ];
      let Kr = {};
      function ev(n) {
        return (
          n in Kr ||
            (Kr[n] =
              pe.ng &&
              pe.ng.common &&
              pe.ng.common.locales &&
              pe.ng.common.locales[n]),
          Kr[n]
        );
      }
      var S = (() => (
        ((S = S || {})[(S.LocaleId = 0)] = "LocaleId"),
        (S[(S.DayPeriodsFormat = 1)] = "DayPeriodsFormat"),
        (S[(S.DayPeriodsStandalone = 2)] = "DayPeriodsStandalone"),
        (S[(S.DaysFormat = 3)] = "DaysFormat"),
        (S[(S.DaysStandalone = 4)] = "DaysStandalone"),
        (S[(S.MonthsFormat = 5)] = "MonthsFormat"),
        (S[(S.MonthsStandalone = 6)] = "MonthsStandalone"),
        (S[(S.Eras = 7)] = "Eras"),
        (S[(S.FirstDayOfWeek = 8)] = "FirstDayOfWeek"),
        (S[(S.WeekendRange = 9)] = "WeekendRange"),
        (S[(S.DateFormat = 10)] = "DateFormat"),
        (S[(S.TimeFormat = 11)] = "TimeFormat"),
        (S[(S.DateTimeFormat = 12)] = "DateTimeFormat"),
        (S[(S.NumberSymbols = 13)] = "NumberSymbols"),
        (S[(S.NumberFormats = 14)] = "NumberFormats"),
        (S[(S.CurrencyCode = 15)] = "CurrencyCode"),
        (S[(S.CurrencySymbol = 16)] = "CurrencySymbol"),
        (S[(S.CurrencyName = 17)] = "CurrencyName"),
        (S[(S.Currencies = 18)] = "Currencies"),
        (S[(S.Directionality = 19)] = "Directionality"),
        (S[(S.PluralCase = 20)] = "PluralCase"),
        (S[(S.ExtraData = 21)] = "ExtraData"),
        S
      ))();
      const Ka = "en-US";
      let tv = Ka;
      function Fd(n, e, t, i, r) {
        if (((n = z(n)), Array.isArray(n)))
          for (let s = 0; s < n.length; s++) Fd(n[s], e, t, i, r);
        else {
          const s = ie(),
            o = C();
          let a = Pr(n) ? n : z(n.provide),
            l = O_(n);
          const c = Ye(),
            u = 1048575 & c.providerIndexes,
            d = c.directiveStart,
            h = c.providerIndexes >> 20;
          if (Pr(n) || !n.multi) {
            const f = new Is(l, r, _),
              p = Pd(a, e, r ? u : u + h, d);
            -1 === p
              ? (Ca(ks(c, o), s, a),
                Rd(s, n, e.length),
                e.push(a),
                c.directiveStart++,
                c.directiveEnd++,
                r && (c.providerIndexes += 1048576),
                t.push(f),
                o.push(f))
              : ((t[p] = f), (o[p] = f));
          } else {
            const f = Pd(a, e, u + h, d),
              p = Pd(a, e, u, u + h),
              g = f >= 0 && t[f],
              y = p >= 0 && t[p];
            if ((r && !y) || (!r && !g)) {
              Ca(ks(c, o), s, a);
              const v = (function Kx(n, e, t, i, r) {
                const s = new Is(n, t, _);
                return (
                  (s.multi = []),
                  (s.index = e),
                  (s.componentProviders = 0),
                  Mv(s, r, i && !t),
                  s
                );
              })(r ? Wx : qx, t.length, r, i, l);
              !r && y && (t[p].providerFactory = v),
                Rd(s, n, e.length, 0),
                e.push(a),
                c.directiveStart++,
                c.directiveEnd++,
                r && (c.providerIndexes += 1048576),
                t.push(v),
                o.push(v);
            } else Rd(s, n, f > -1 ? f : p, Mv(t[r ? p : f], l, !r && i));
            !r && i && y && t[p].componentProviders++;
          }
        }
      }
      function Rd(n, e, t, i) {
        const r = Pr(e),
          s = (function vO(n) {
            return !!n.useClass;
          })(e);
        if (r || s) {
          const l = (s ? z(e.useClass) : e).prototype.ngOnDestroy;
          if (l) {
            const c = n.destroyHooks || (n.destroyHooks = []);
            if (!r && e.multi) {
              const u = c.indexOf(t);
              -1 === u ? c.push(t, [i, l]) : c[u + 1].push(i, l);
            } else c.push(t, l);
          }
        }
      }
      function Mv(n, e, t) {
        return t && n.componentProviders++, n.multi.push(e) - 1;
      }
      function Pd(n, e, t, i) {
        for (let r = t; r < i; r++) if (e[r] === n) return r;
        return -1;
      }
      function qx(n, e, t, i) {
        return Nd(this.multi, []);
      }
      function Wx(n, e, t, i) {
        const r = this.multi;
        let s;
        if (this.providerFactory) {
          const o = this.providerFactory.componentProviders,
            a = Fs(t, t[1], this.providerFactory.index, i);
          (s = a.slice(0, o)), Nd(r, s);
          for (let l = o; l < a.length; l++) s.push(a[l]);
        } else (s = []), Nd(r, s);
        return s;
      }
      function Nd(n, e) {
        for (let t = 0; t < n.length; t++) e.push((0, n[t])());
        return e;
      }
      function ge(n, e = []) {
        return (t) => {
          t.providersResolver = (i, r) =>
            (function Gx(n, e, t) {
              const i = ie();
              if (i.firstCreatePass) {
                const r = un(n);
                Fd(t, i.data, i.blueprint, r, !0),
                  Fd(e, i.data, i.blueprint, r, !1);
              }
            })(i, r ? r(n) : n, e);
        };
      }
      class Sv {}
      class Qx {
        resolveComponentFactory(e) {
          throw (function Zx(n) {
            const e = Error(
              `No component factory found for ${de(
                n
              )}. Did you add it to @NgModule.entryComponents?`
            );
            return (e.ngComponent = n), e;
          })(e);
        }
      }
      let $i = (() => {
        class n {}
        return (n.NULL = new Qx()), n;
      })();
      function Xx() {
        return Zr(Ye(), C());
      }
      function Zr(n, e) {
        return new Se(Wt(n, e));
      }
      let Se = (() => {
        class n {
          constructor(t) {
            this.nativeElement = t;
          }
        }
        return (n.__NG_ELEMENT_ID__ = Xx), n;
      })();
      function Jx(n) {
        return n instanceof Se ? n.nativeElement : n;
      }
      class ao {}
      let Yn = (() => {
          class n {}
          return (
            (n.__NG_ELEMENT_ID__ = () =>
              (function tk() {
                const n = C(),
                  t = It(Ye().index, n);
                return (function ek(n) {
                  return n[G];
                })(En(t) ? t : n);
              })()),
            n
          );
        })(),
        nk = (() => {
          class n {}
          return (
            (n.ɵprov = I({
              token: n,
              providedIn: "root",
              factory: () => null,
            })),
            n
          );
        })();
      class zi {
        constructor(e) {
          (this.full = e),
            (this.major = e.split(".")[0]),
            (this.minor = e.split(".")[1]),
            (this.patch = e.split(".").slice(2).join("."));
        }
      }
      const ik = new zi("13.1.3"),
        Ld = {};
      function Ja(n, e, t, i, r = !1) {
        for (; null !== t; ) {
          const s = e[t.index];
          if ((null !== s && i.push(He(s)), cn(s)))
            for (let a = 10; a < s.length; a++) {
              const l = s[a],
                c = l[1].firstChild;
              null !== c && Ja(l[1], l, c, i);
            }
          const o = t.type;
          if (8 & o) Ja(n, e, t.child, i);
          else if (32 & o) {
            const a = Ru(t, e);
            let l;
            for (; (l = a()); ) i.push(l);
          } else if (16 & o) {
            const a = Vm(e, t);
            if (Array.isArray(a)) i.push(...a);
            else {
              const l = qs(e[16]);
              Ja(l[1], l, a, i, !0);
            }
          }
          t = r ? t.projectionNext : t.next;
        }
        return i;
      }
      class lo {
        constructor(e, t) {
          (this._lView = e),
            (this._cdRefInjectingView = t),
            (this._appRef = null),
            (this._attachedToViewContainer = !1);
        }
        get rootNodes() {
          const e = this._lView,
            t = e[1];
          return Ja(t, e, t.firstChild, []);
        }
        get context() {
          return this._lView[8];
        }
        set context(e) {
          this._lView[8] = e;
        }
        get destroyed() {
          return 256 == (256 & this._lView[2]);
        }
        destroy() {
          if (this._appRef) this._appRef.detachView(this);
          else if (this._attachedToViewContainer) {
            const e = this._lView[3];
            if (cn(e)) {
              const t = e[8],
                i = t ? t.indexOf(this) : -1;
              i > -1 && (Bu(e, i), Da(t, i));
            }
            this._attachedToViewContainer = !1;
          }
          Om(this._lView[1], this._lView);
        }
        onDestroy(e) {
          u_(this._lView[1], this._lView, null, e);
        }
        markForCheck() {
          ld(this._cdRefInjectingView || this._lView);
        }
        detach() {
          this._lView[2] &= -129;
        }
        reattach() {
          this._lView[2] |= 128;
        }
        detectChanges() {
          ud(this._lView[1], this._lView, this.context);
        }
        checkNoChanges() {
          !(function lO(n, e, t) {
            da(!0);
            try {
              ud(n, e, t);
            } finally {
              da(!1);
            }
          })(this._lView[1], this._lView, this.context);
        }
        attachToViewContainerRef() {
          if (this._appRef) throw new ne(902, "");
          this._attachedToViewContainer = !0;
        }
        detachFromAppRef() {
          (this._appRef = null),
            (function rT(n, e) {
              Ws(n, e, e[G], 2, null, null);
            })(this._lView[1], this._lView);
        }
        attachToAppRef(e) {
          if (this._attachedToViewContainer) throw new ne(902, "");
          this._appRef = e;
        }
      }
      class rk extends lo {
        constructor(e) {
          super(e), (this._view = e);
        }
        detectChanges() {
          v_(this._view);
        }
        checkNoChanges() {
          !(function cO(n) {
            da(!0);
            try {
              v_(n);
            } finally {
              da(!1);
            }
          })(this._view);
        }
        get context() {
          return null;
        }
      }
      class Tv extends $i {
        constructor(e) {
          super(), (this.ngModule = e);
        }
        resolveComponentFactory(e) {
          const t = st(e);
          return new Vd(t, this.ngModule);
        }
      }
      function Ov(n) {
        const e = [];
        for (let t in n)
          n.hasOwnProperty(t) && e.push({ propName: n[t], templateName: t });
        return e;
      }
      const ok = new T("SCHEDULER_TOKEN", {
        providedIn: "root",
        factory: () => Cm,
      });
      class Vd extends Sv {
        constructor(e, t) {
          super(),
            (this.componentDef = e),
            (this.ngModule = t),
            (this.componentType = e.type),
            (this.selector = (function ET(n) {
              return n.map(DT).join(",");
            })(e.selectors)),
            (this.ngContentSelectors = e.ngContentSelectors
              ? e.ngContentSelectors
              : []),
            (this.isBoundToModule = !!t);
        }
        get inputs() {
          return Ov(this.componentDef.inputs);
        }
        get outputs() {
          return Ov(this.componentDef.outputs);
        }
        create(e, t, i, r) {
          const s = (r = r || this.ngModule)
              ? (function ak(n, e) {
                  return {
                    get: (t, i, r) => {
                      const s = n.get(t, Ld, r);
                      return s !== Ld || i === Ld ? s : e.get(t, i, r);
                    },
                  };
                })(e, r.injector)
              : e,
            o = s.get(ao, yg),
            a = s.get(nk, null),
            l = o.createRenderer(null, this.componentDef),
            c = this.componentDef.selectors[0][0] || "div",
            u = i
              ? (function c_(n, e, t) {
                  if (Re(n)) return n.selectRootElement(e, t === an.ShadowDom);
                  let i = "string" == typeof e ? n.querySelector(e) : e;
                  return (i.textContent = ""), i;
                })(l, i, this.componentDef.encapsulation)
              : Vu(
                  o.createRenderer(null, this.componentDef),
                  c,
                  (function sk(n) {
                    const e = n.toLowerCase();
                    return "svg" === e
                      ? "http://www.w3.org/2000/svg"
                      : "math" === e
                      ? "http://www.w3.org/1998/MathML/"
                      : null;
                  })(c)
                ),
            d = this.componentDef.onPush ? 576 : 528,
            h = (function H_(n, e) {
              return {
                components: [],
                scheduler: n || Cm,
                clean: uO,
                playerHandler: e || null,
                flags: 0,
              };
            })(),
            f = La(0, null, null, 1, 0, null, null, null, null, null),
            p = Ks(null, f, h, d, null, null, o, l, a, s);
          let g, y;
          ha(p);
          try {
            const v = (function B_(n, e, t, i, r, s) {
              const o = t[1];
              t[20] = n;
              const l = xr(o, 20, 2, "#host", null),
                c = (l.mergedAttrs = e.hostAttrs);
              null !== c &&
                (Ba(l, c, !0),
                null !== n &&
                  (_a(r, n, c),
                  null !== l.classes && zu(r, n, l.classes),
                  null !== l.styles && Hm(r, n, l.styles)));
              const u = i.createRenderer(n, e),
                d = Ks(
                  t,
                  a_(e),
                  null,
                  e.onPush ? 64 : 16,
                  t[20],
                  l,
                  i,
                  u,
                  s || null,
                  null
                );
              return (
                o.firstCreatePass &&
                  (Ca(ks(l, t), o, e.type), g_(o, l), m_(l, t.length, 1)),
                Va(t, d),
                (t[20] = d)
              );
            })(u, this.componentDef, p, o, l);
            if (u)
              if (i) _a(l, u, ["ng-version", ik.full]);
              else {
                const { attrs: m, classes: w } = (function MT(n) {
                  const e = [],
                    t = [];
                  let i = 1,
                    r = 2;
                  for (; i < n.length; ) {
                    let s = n[i];
                    if ("string" == typeof s)
                      2 === r
                        ? "" !== s && e.push(s, n[++i])
                        : 8 === r && t.push(s);
                    else {
                      if (!dn(r)) break;
                      r = s;
                    }
                    i++;
                  }
                  return { attrs: e, classes: t };
                })(this.componentDef.selectors[0]);
                m && _a(l, u, m), w && w.length > 0 && zu(l, u, w.join(" "));
              }
            if (((y = tu(f, 20)), void 0 !== t)) {
              const m = (y.projection = []);
              for (let w = 0; w < this.ngContentSelectors.length; w++) {
                const A = t[w];
                m.push(null != A ? Array.from(A) : null);
              }
            }
            (g = (function j_(n, e, t, i, r) {
              const s = t[1],
                o = (function qT(n, e, t) {
                  const i = Ye();
                  n.firstCreatePass &&
                    (t.providersResolver && t.providersResolver(t),
                    __(n, i, e, kr(n, e, 1, null), t));
                  const r = Fs(e, n, i.directiveStart, i);
                  lt(r, e);
                  const s = Wt(i, e);
                  return s && lt(s, e), r;
                })(s, t, e);
              if (
                (i.components.push(o),
                (n[8] = o),
                r && r.forEach((l) => l(o, e)),
                e.contentQueries)
              ) {
                const l = Ye();
                e.contentQueries(1, o, l.directiveStart);
              }
              const a = Ye();
              return (
                !s.firstCreatePass ||
                  (null === e.hostBindings && null === e.hostAttrs) ||
                  (hi(a.index),
                  f_(t[1], a, 0, a.directiveStart, a.directiveEnd, e),
                  p_(e, o)),
                o
              );
            })(v, this.componentDef, p, h, [IO])),
              Ys(f, p, null);
          } finally {
            fa();
          }
          return new ck(this.componentType, g, Zr(y, p), p, y);
        }
      }
      class ck extends class Yx {} {
        constructor(e, t, i, r, s) {
          super(),
            (this.location = i),
            (this._rootLView = r),
            (this._tNode = s),
            (this.instance = t),
            (this.hostView = this.changeDetectorRef = new rk(r)),
            (this.componentType = e);
        }
        get injector() {
          return new yr(this._tNode, this._rootLView);
        }
        destroy() {
          this.hostView.destroy();
        }
        onDestroy(e) {
          this.hostView.onDestroy(e);
        }
      }
      class Zn {}
      class Iv {}
      const Qr = new Map();
      class Fv extends Zn {
        constructor(e, t) {
          super(),
            (this._parent = t),
            (this._bootstrapComponents = []),
            (this.injector = this),
            (this.destroyCbs = []),
            (this.componentFactoryResolver = new Tv(this));
          const i = zt(e);
          (this._bootstrapComponents = On(i.bootstrap)),
            (this._r3Injector = T_(
              e,
              t,
              [
                { provide: Zn, useValue: this },
                { provide: $i, useValue: this.componentFactoryResolver },
              ],
              de(e)
            )),
            this._r3Injector._resolveInjectorDefTypes(),
            (this.instance = this.get(e));
        }
        get(e, t = Qe.THROW_IF_NOT_FOUND, i = U.Default) {
          return e === Qe || e === Zn || e === hd
            ? this
            : this._r3Injector.get(e, t, i);
        }
        destroy() {
          const e = this._r3Injector;
          !e.destroyed && e.destroy(),
            this.destroyCbs.forEach((t) => t()),
            (this.destroyCbs = null);
        }
        onDestroy(e) {
          this.destroyCbs.push(e);
        }
      }
      class Bd extends Iv {
        constructor(e) {
          super(),
            (this.moduleType = e),
            null !== zt(e) &&
              (function dk(n) {
                const e = new Set();
                !(function t(i) {
                  const r = zt(i, !0),
                    s = r.id;
                  null !== s &&
                    ((function xv(n, e, t) {
                      if (e && e !== t)
                        throw new Error(
                          `Duplicate module registered for ${n} - ${de(
                            e
                          )} vs ${de(e.name)}`
                        );
                    })(s, Qr.get(s), i),
                    Qr.set(s, i));
                  const o = On(r.imports);
                  for (const a of o) e.has(a) || (e.add(a), t(a));
                })(n);
              })(e);
        }
        create(e) {
          return new Fv(this.moduleType, e);
        }
      }
      function jd(n) {
        return (e) => {
          setTimeout(n, void 0, e);
        };
      }
      const Q = class Ok extends le {
        constructor(e = !1) {
          super(), (this.__isAsync = e);
        }
        emit(e) {
          super.next(e);
        }
        subscribe(e, t, i) {
          var r, s, o;
          let a = e,
            l = t || (() => null),
            c = i;
          if (e && "object" == typeof e) {
            const d = e;
            (a = null === (r = d.next) || void 0 === r ? void 0 : r.bind(d)),
              (l = null === (s = d.error) || void 0 === s ? void 0 : s.bind(d)),
              (c =
                null === (o = d.complete) || void 0 === o ? void 0 : o.bind(d));
          }
          this.__isAsync && ((l = jd(l)), a && (a = jd(a)), c && (c = jd(c)));
          const u = super.subscribe({ next: a, error: l, complete: c });
          return e instanceof Le && e.add(u), u;
        }
      };
      function Ik() {
        return this._results[Nr()]();
      }
      class ho {
        constructor(e = !1) {
          (this._emitDistinctChangesOnly = e),
            (this.dirty = !0),
            (this._results = []),
            (this._changesDetected = !1),
            (this._changes = null),
            (this.length = 0),
            (this.first = void 0),
            (this.last = void 0);
          const t = Nr(),
            i = ho.prototype;
          i[t] || (i[t] = Ik);
        }
        get changes() {
          return this._changes || (this._changes = new Q());
        }
        get(e) {
          return this._results[e];
        }
        map(e) {
          return this._results.map(e);
        }
        filter(e) {
          return this._results.filter(e);
        }
        find(e) {
          return this._results.find(e);
        }
        reduce(e, t) {
          return this._results.reduce(e, t);
        }
        forEach(e) {
          this._results.forEach(e);
        }
        some(e) {
          return this._results.some(e);
        }
        toArray() {
          return this._results.slice();
        }
        toString() {
          return this._results.toString();
        }
        reset(e, t) {
          const i = this;
          i.dirty = !1;
          const r = Kt(e);
          (this._changesDetected = !(function NS(n, e, t) {
            if (n.length !== e.length) return !1;
            for (let i = 0; i < n.length; i++) {
              let r = n[i],
                s = e[i];
              if ((t && ((r = t(r)), (s = t(s))), s !== r)) return !1;
            }
            return !0;
          })(i._results, r, t)) &&
            ((i._results = r),
            (i.length = r.length),
            (i.last = r[this.length - 1]),
            (i.first = r[0]));
        }
        notifyOnChanges() {
          this._changes &&
            (this._changesDetected || !this._emitDistinctChangesOnly) &&
            this._changes.emit(this);
        }
        setDirty() {
          this.dirty = !0;
        }
        destroy() {
          this.changes.complete(), this.changes.unsubscribe();
        }
      }
      Symbol;
      let Rn = (() => {
        class n {}
        return (n.__NG_ELEMENT_ID__ = Fk), n;
      })();
      const xk = Rn,
        kk = class extends xk {
          constructor(e, t, i) {
            super(),
              (this._declarationLView = e),
              (this._declarationTContainer = t),
              (this.elementRef = i);
          }
          createEmbeddedView(e) {
            const t = this._declarationTContainer.tViews,
              i = Ks(
                this._declarationLView,
                t,
                e,
                16,
                null,
                t.declTNode,
                null,
                null,
                null,
                null
              );
            i[17] = this._declarationLView[this._declarationTContainer.index];
            const s = this._declarationLView[19];
            return (
              null !== s && (i[19] = s.createEmbeddedView(t)),
              Ys(t, i, e),
              new lo(i)
            );
          }
        };
      function Fk() {
        return el(Ye(), C());
      }
      function el(n, e) {
        return 4 & n.type ? new kk(e, n, Zr(n, e)) : null;
      }
      let Zt = (() => {
        class n {}
        return (n.__NG_ELEMENT_ID__ = Rk), n;
      })();
      function Rk() {
        return Hv(Ye(), C());
      }
      const Pk = Zt,
        Bv = class extends Pk {
          constructor(e, t, i) {
            super(),
              (this._lContainer = e),
              (this._hostTNode = t),
              (this._hostLView = i);
          }
          get element() {
            return Zr(this._hostTNode, this._hostLView);
          }
          get injector() {
            return new yr(this._hostTNode, this._hostLView);
          }
          get parentInjector() {
            const e = ba(this._hostTNode, this._hostLView);
            if (Rg(e)) {
              const t = _r(e, this._hostLView),
                i = mr(e);
              return new yr(t[1].data[i + 8], t);
            }
            return new yr(null, this._hostLView);
          }
          clear() {
            for (; this.length > 0; ) this.remove(this.length - 1);
          }
          get(e) {
            const t = jv(this._lContainer);
            return (null !== t && t[e]) || null;
          }
          get length() {
            return this._lContainer.length - 10;
          }
          createEmbeddedView(e, t, i) {
            const r = e.createEmbeddedView(t || {});
            return this.insert(r, i), r;
          }
          createComponent(e, t, i, r, s) {
            const o =
              e &&
              !(function Ps(n) {
                return "function" == typeof n;
              })(e);
            let a;
            if (o) a = t;
            else {
              const d = t || {};
              (a = d.index),
                (i = d.injector),
                (r = d.projectableNodes),
                (s = d.ngModuleRef);
            }
            const l = o ? e : new Vd(st(e)),
              c = i || this.parentInjector;
            if (!s && null == l.ngModule && c) {
              const d = c.get(Zn, null);
              d && (s = d);
            }
            const u = l.create(c, r, void 0, s);
            return this.insert(u.hostView, a), u;
          }
          insert(e, t) {
            const i = e._lView,
              r = i[1];
            if (
              (function iS(n) {
                return cn(n[3]);
              })(i)
            ) {
              const u = this.indexOf(e);
              if (-1 !== u) this.detach(u);
              else {
                const d = i[3],
                  h = new Bv(d, d[6], d[3]);
                h.detach(h.indexOf(e));
              }
            }
            const s = this._adjustIndex(t),
              o = this._lContainer;
            !(function oT(n, e, t, i) {
              const r = 10 + i,
                s = t.length;
              i > 0 && (t[r - 1][4] = e),
                i < s - 10
                  ? ((e[4] = t[r]), zg(t, 10 + i, e))
                  : (t.push(e), (e[4] = null)),
                (e[3] = t);
              const o = e[17];
              null !== o &&
                t !== o &&
                (function aT(n, e) {
                  const t = n[9];
                  e[16] !== e[3][3][16] && (n[2] = !0),
                    null === t ? (n[9] = [e]) : t.push(e);
                })(o, e);
              const a = e[19];
              null !== a && a.insertView(n), (e[2] |= 128);
            })(r, i, o, s);
            const a = Uu(s, o),
              l = i[G],
              c = xa(l, o[7]);
            return (
              null !== c &&
                (function iT(n, e, t, i, r, s) {
                  (i[0] = r), (i[6] = e), Ws(n, i, t, 1, r, s);
                })(r, o[6], l, i, c, a),
              e.attachToViewContainerRef(),
              zg(Hd(o), s, e),
              e
            );
          }
          move(e, t) {
            return this.insert(e, t);
          }
          indexOf(e) {
            const t = jv(this._lContainer);
            return null !== t ? t.indexOf(e) : -1;
          }
          remove(e) {
            const t = this._adjustIndex(e, -1),
              i = Bu(this._lContainer, t);
            i && (Da(Hd(this._lContainer), t), Om(i[1], i));
          }
          detach(e) {
            const t = this._adjustIndex(e, -1),
              i = Bu(this._lContainer, t);
            return i && null != Da(Hd(this._lContainer), t) ? new lo(i) : null;
          }
          _adjustIndex(e, t = 0) {
            return null == e ? this.length + t : e;
          }
        };
      function jv(n) {
        return n[8];
      }
      function Hd(n) {
        return n[8] || (n[8] = []);
      }
      function Hv(n, e) {
        let t;
        const i = e[n.index];
        if (cn(i)) t = i;
        else {
          let r;
          if (8 & n.type) r = He(i);
          else {
            const s = e[G];
            r = s.createComment("");
            const o = Wt(n, e);
            ji(
              s,
              xa(s, o),
              r,
              (function dT(n, e) {
                return Re(n) ? n.nextSibling(e) : e.nextSibling;
              })(s, o),
              !1
            );
          }
          (e[n.index] = t = y_(i, e, r, n)), Va(e, t);
        }
        return new Bv(t, n, e);
      }
      class Ud {
        constructor(e) {
          (this.queryList = e), (this.matches = null);
        }
        clone() {
          return new Ud(this.queryList);
        }
        setDirty() {
          this.queryList.setDirty();
        }
      }
      class $d {
        constructor(e = []) {
          this.queries = e;
        }
        createEmbeddedView(e) {
          const t = e.queries;
          if (null !== t) {
            const i =
                null !== e.contentQueries ? e.contentQueries[0] : t.length,
              r = [];
            for (let s = 0; s < i; s++) {
              const o = t.getByIndex(s);
              r.push(this.queries[o.indexInDeclarationView].clone());
            }
            return new $d(r);
          }
          return null;
        }
        insertView(e) {
          this.dirtyQueriesWithMatches(e);
        }
        detachView(e) {
          this.dirtyQueriesWithMatches(e);
        }
        dirtyQueriesWithMatches(e) {
          for (let t = 0; t < this.queries.length; t++)
            null !== qv(e, t).matches && this.queries[t].setDirty();
        }
      }
      class Uv {
        constructor(e, t, i = null) {
          (this.predicate = e), (this.flags = t), (this.read = i);
        }
      }
      class zd {
        constructor(e = []) {
          this.queries = e;
        }
        elementStart(e, t) {
          for (let i = 0; i < this.queries.length; i++)
            this.queries[i].elementStart(e, t);
        }
        elementEnd(e) {
          for (let t = 0; t < this.queries.length; t++)
            this.queries[t].elementEnd(e);
        }
        embeddedTView(e) {
          let t = null;
          for (let i = 0; i < this.length; i++) {
            const r = null !== t ? t.length : 0,
              s = this.getByIndex(i).embeddedTView(e, r);
            s &&
              ((s.indexInDeclarationView = i),
              null !== t ? t.push(s) : (t = [s]));
          }
          return null !== t ? new zd(t) : null;
        }
        template(e, t) {
          for (let i = 0; i < this.queries.length; i++)
            this.queries[i].template(e, t);
        }
        getByIndex(e) {
          return this.queries[e];
        }
        get length() {
          return this.queries.length;
        }
        track(e) {
          this.queries.push(e);
        }
      }
      class Gd {
        constructor(e, t = -1) {
          (this.metadata = e),
            (this.matches = null),
            (this.indexInDeclarationView = -1),
            (this.crossesNgTemplate = !1),
            (this._appliesToNextNode = !0),
            (this._declarationNodeIndex = t);
        }
        elementStart(e, t) {
          this.isApplyingToNode(t) && this.matchTNode(e, t);
        }
        elementEnd(e) {
          this._declarationNodeIndex === e.index &&
            (this._appliesToNextNode = !1);
        }
        template(e, t) {
          this.elementStart(e, t);
        }
        embeddedTView(e, t) {
          return this.isApplyingToNode(e)
            ? ((this.crossesNgTemplate = !0),
              this.addMatch(-e.index, t),
              new Gd(this.metadata))
            : null;
        }
        isApplyingToNode(e) {
          if (this._appliesToNextNode && 1 != (1 & this.metadata.flags)) {
            const t = this._declarationNodeIndex;
            let i = e.parent;
            for (; null !== i && 8 & i.type && i.index !== t; ) i = i.parent;
            return t === (null !== i ? i.index : -1);
          }
          return this._appliesToNextNode;
        }
        matchTNode(e, t) {
          const i = this.metadata.predicate;
          if (Array.isArray(i))
            for (let r = 0; r < i.length; r++) {
              const s = i[r];
              this.matchTNodeWithReadOption(e, t, Vk(t, s)),
                this.matchTNodeWithReadOption(e, t, wa(t, e, s, !1, !1));
            }
          else
            i === Rn
              ? 4 & t.type && this.matchTNodeWithReadOption(e, t, -1)
              : this.matchTNodeWithReadOption(e, t, wa(t, e, i, !1, !1));
        }
        matchTNodeWithReadOption(e, t, i) {
          if (null !== i) {
            const r = this.metadata.read;
            if (null !== r)
              if (r === Se || r === Zt || (r === Rn && 4 & t.type))
                this.addMatch(t.index, -2);
              else {
                const s = wa(t, e, r, !1, !1);
                null !== s && this.addMatch(t.index, s);
              }
            else this.addMatch(t.index, i);
          }
        }
        addMatch(e, t) {
          null === this.matches
            ? (this.matches = [e, t])
            : this.matches.push(e, t);
        }
      }
      function Vk(n, e) {
        const t = n.localNames;
        if (null !== t)
          for (let i = 0; i < t.length; i += 2) if (t[i] === e) return t[i + 1];
        return null;
      }
      function jk(n, e, t, i) {
        return -1 === t
          ? (function Bk(n, e) {
              return 11 & n.type ? Zr(n, e) : 4 & n.type ? el(n, e) : null;
            })(e, n)
          : -2 === t
          ? (function Hk(n, e, t) {
              return t === Se
                ? Zr(e, n)
                : t === Rn
                ? el(e, n)
                : t === Zt
                ? Hv(e, n)
                : void 0;
            })(n, e, i)
          : Fs(n, n[1], t, e);
      }
      function $v(n, e, t, i) {
        const r = e[19].queries[i];
        if (null === r.matches) {
          const s = n.data,
            o = t.matches,
            a = [];
          for (let l = 0; l < o.length; l += 2) {
            const c = o[l];
            a.push(c < 0 ? null : jk(e, s[c], o[l + 1], t.metadata.read));
          }
          r.matches = a;
        }
        return r.matches;
      }
      function qd(n, e, t, i) {
        const r = n.queries.getByIndex(t),
          s = r.matches;
        if (null !== s) {
          const o = $v(n, e, r, t);
          for (let a = 0; a < s.length; a += 2) {
            const l = s[a];
            if (l > 0) i.push(o[a / 2]);
            else {
              const c = s[a + 1],
                u = e[-l];
              for (let d = 10; d < u.length; d++) {
                const h = u[d];
                h[17] === h[3] && qd(h[1], h, c, i);
              }
              if (null !== u[9]) {
                const d = u[9];
                for (let h = 0; h < d.length; h++) {
                  const f = d[h];
                  qd(f[1], f, c, i);
                }
              }
            }
          }
        }
        return i;
      }
      function Te(n) {
        const e = C(),
          t = ie(),
          i = Mg();
        lu(i + 1);
        const r = qv(t, i);
        if (n.dirty && vg(e) === (2 == (2 & r.metadata.flags))) {
          if (null === r.matches) n.reset([]);
          else {
            const s = r.crossesNgTemplate ? qd(t, e, i, []) : $v(t, e, r, i);
            n.reset(s, Jx), n.notifyOnChanges();
          }
          return !0;
        }
        return !1;
      }
      function yi(n, e, t) {
        const i = ie();
        i.firstCreatePass &&
          (Gv(i, new Uv(n, e, t), -1),
          2 == (2 & e) && (i.staticViewQueries = !0)),
          zv(i, C(), e);
      }
      function ut(n, e, t, i) {
        const r = ie();
        if (r.firstCreatePass) {
          const s = Ye();
          Gv(r, new Uv(e, t, i), s.index),
            (function $k(n, e) {
              const t = n.contentQueries || (n.contentQueries = []);
              e !== (t.length ? t[t.length - 1] : -1) &&
                t.push(n.queries.length - 1, e);
            })(r, n),
            2 == (2 & t) && (r.staticContentQueries = !0);
        }
        zv(r, C(), t);
      }
      function Oe() {
        return (function Uk(n, e) {
          return n[19].queries[e].queryList;
        })(C(), Mg());
      }
      function zv(n, e, t) {
        const i = new ho(4 == (4 & t));
        u_(n, e, i, i.destroy),
          null === e[19] && (e[19] = new $d()),
          e[19].queries.push(new Ud(i));
      }
      function Gv(n, e, t) {
        null === n.queries && (n.queries = new zd()),
          n.queries.track(new Gd(e, t));
      }
      function qv(n, e) {
        return n.queries.getByIndex(e);
      }
      function il(...n) {}
      const rl = new T("Application Initializer");
      let Jr = (() => {
        class n {
          constructor(t) {
            (this.appInits = t),
              (this.resolve = il),
              (this.reject = il),
              (this.initialized = !1),
              (this.done = !1),
              (this.donePromise = new Promise((i, r) => {
                (this.resolve = i), (this.reject = r);
              }));
          }
          runInitializers() {
            if (this.initialized) return;
            const t = [],
              i = () => {
                (this.done = !0), this.resolve();
              };
            if (this.appInits)
              for (let r = 0; r < this.appInits.length; r++) {
                const s = this.appInits[r]();
                if (Js(s)) t.push(s);
                else if (Sd(s)) {
                  const o = new Promise((a, l) => {
                    s.subscribe({ complete: a, error: l });
                  });
                  t.push(o);
                }
              }
            Promise.all(t)
              .then(() => {
                i();
              })
              .catch((r) => {
                this.reject(r);
              }),
              0 === t.length && i(),
              (this.initialized = !0);
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(rl, 8));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      const po = new T("AppId"),
        lF = {
          provide: po,
          useFactory: function aF() {
            return `${Xd()}${Xd()}${Xd()}`;
          },
          deps: [],
        };
      function Xd() {
        return String.fromCharCode(97 + Math.floor(25 * Math.random()));
      }
      const cb = new T("Platform Initializer"),
        go = new T("Platform ID"),
        ub = new T("appBootstrapListener");
      let db = (() => {
        class n {
          log(t) {
            console.log(t);
          }
          warn(t) {
            console.warn(t);
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      const Qn = new T("LocaleId"),
        hb = new T("DefaultCurrencyCode");
      class cF {
        constructor(e, t) {
          (this.ngModuleFactory = e), (this.componentFactories = t);
        }
      }
      let sl = (() => {
        class n {
          compileModuleSync(t) {
            return new Bd(t);
          }
          compileModuleAsync(t) {
            return Promise.resolve(this.compileModuleSync(t));
          }
          compileModuleAndAllComponentsSync(t) {
            const i = this.compileModuleSync(t),
              s = On(zt(t).declarations).reduce((o, a) => {
                const l = st(a);
                return l && o.push(new Vd(l)), o;
              }, []);
            return new cF(i, s);
          }
          compileModuleAndAllComponentsAsync(t) {
            return Promise.resolve(this.compileModuleAndAllComponentsSync(t));
          }
          clearCache() {}
          clearCacheFor(t) {}
          getModuleId(t) {}
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      const dF = (() => Promise.resolve(0))();
      function Jd(n) {
        "undefined" == typeof Zone
          ? dF.then(() => {
              n && n.apply(null, null);
            })
          : Zone.current.scheduleMicroTask("scheduleMicrotask", n);
      }
      class ee {
        constructor({
          enableLongStackTrace: e = !1,
          shouldCoalesceEventChangeDetection: t = !1,
          shouldCoalesceRunChangeDetection: i = !1,
        }) {
          if (
            ((this.hasPendingMacrotasks = !1),
            (this.hasPendingMicrotasks = !1),
            (this.isStable = !0),
            (this.onUnstable = new Q(!1)),
            (this.onMicrotaskEmpty = new Q(!1)),
            (this.onStable = new Q(!1)),
            (this.onError = new Q(!1)),
            "undefined" == typeof Zone)
          )
            throw new Error("In this configuration Angular requires Zone.js");
          Zone.assertZonePatched();
          const r = this;
          (r._nesting = 0),
            (r._outer = r._inner = Zone.current),
            Zone.TaskTrackingZoneSpec &&
              (r._inner = r._inner.fork(new Zone.TaskTrackingZoneSpec())),
            e &&
              Zone.longStackTraceZoneSpec &&
              (r._inner = r._inner.fork(Zone.longStackTraceZoneSpec)),
            (r.shouldCoalesceEventChangeDetection = !i && t),
            (r.shouldCoalesceRunChangeDetection = i),
            (r.lastRequestAnimationFrameId = -1),
            (r.nativeRequestAnimationFrame = (function hF() {
              let n = pe.requestAnimationFrame,
                e = pe.cancelAnimationFrame;
              if ("undefined" != typeof Zone && n && e) {
                const t = n[Zone.__symbol__("OriginalDelegate")];
                t && (n = t);
                const i = e[Zone.__symbol__("OriginalDelegate")];
                i && (e = i);
              }
              return {
                nativeRequestAnimationFrame: n,
                nativeCancelAnimationFrame: e,
              };
            })().nativeRequestAnimationFrame),
            (function gF(n) {
              const e = () => {
                !(function pF(n) {
                  n.isCheckStableRunning ||
                    -1 !== n.lastRequestAnimationFrameId ||
                    ((n.lastRequestAnimationFrameId =
                      n.nativeRequestAnimationFrame.call(pe, () => {
                        n.fakeTopEventTask ||
                          (n.fakeTopEventTask = Zone.root.scheduleEventTask(
                            "fakeTopEventTask",
                            () => {
                              (n.lastRequestAnimationFrameId = -1),
                                th(n),
                                (n.isCheckStableRunning = !0),
                                eh(n),
                                (n.isCheckStableRunning = !1);
                            },
                            void 0,
                            () => {},
                            () => {}
                          )),
                          n.fakeTopEventTask.invoke();
                      })),
                    th(n));
                })(n);
              };
              n._inner = n._inner.fork({
                name: "angular",
                properties: { isAngularZone: !0 },
                onInvokeTask: (t, i, r, s, o, a) => {
                  try {
                    return fb(n), t.invokeTask(r, s, o, a);
                  } finally {
                    ((n.shouldCoalesceEventChangeDetection &&
                      "eventTask" === s.type) ||
                      n.shouldCoalesceRunChangeDetection) &&
                      e(),
                      pb(n);
                  }
                },
                onInvoke: (t, i, r, s, o, a, l) => {
                  try {
                    return fb(n), t.invoke(r, s, o, a, l);
                  } finally {
                    n.shouldCoalesceRunChangeDetection && e(), pb(n);
                  }
                },
                onHasTask: (t, i, r, s) => {
                  t.hasTask(r, s),
                    i === r &&
                      ("microTask" == s.change
                        ? ((n._hasPendingMicrotasks = s.microTask),
                          th(n),
                          eh(n))
                        : "macroTask" == s.change &&
                          (n.hasPendingMacrotasks = s.macroTask));
                },
                onHandleError: (t, i, r, s) => (
                  t.handleError(r, s),
                  n.runOutsideAngular(() => n.onError.emit(s)),
                  !1
                ),
              });
            })(r);
        }
        static isInAngularZone() {
          return !0 === Zone.current.get("isAngularZone");
        }
        static assertInAngularZone() {
          if (!ee.isInAngularZone())
            throw new Error("Expected to be in Angular Zone, but it is not!");
        }
        static assertNotInAngularZone() {
          if (ee.isInAngularZone())
            throw new Error("Expected to not be in Angular Zone, but it is!");
        }
        run(e, t, i) {
          return this._inner.run(e, t, i);
        }
        runTask(e, t, i, r) {
          const s = this._inner,
            o = s.scheduleEventTask("NgZoneEvent: " + r, e, fF, il, il);
          try {
            return s.runTask(o, t, i);
          } finally {
            s.cancelTask(o);
          }
        }
        runGuarded(e, t, i) {
          return this._inner.runGuarded(e, t, i);
        }
        runOutsideAngular(e) {
          return this._outer.run(e);
        }
      }
      const fF = {};
      function eh(n) {
        if (0 == n._nesting && !n.hasPendingMicrotasks && !n.isStable)
          try {
            n._nesting++, n.onMicrotaskEmpty.emit(null);
          } finally {
            if ((n._nesting--, !n.hasPendingMicrotasks))
              try {
                n.runOutsideAngular(() => n.onStable.emit(null));
              } finally {
                n.isStable = !0;
              }
          }
      }
      function th(n) {
        n.hasPendingMicrotasks = !!(
          n._hasPendingMicrotasks ||
          ((n.shouldCoalesceEventChangeDetection ||
            n.shouldCoalesceRunChangeDetection) &&
            -1 !== n.lastRequestAnimationFrameId)
        );
      }
      function fb(n) {
        n._nesting++,
          n.isStable && ((n.isStable = !1), n.onUnstable.emit(null));
      }
      function pb(n) {
        n._nesting--, eh(n);
      }
      class mF {
        constructor() {
          (this.hasPendingMicrotasks = !1),
            (this.hasPendingMacrotasks = !1),
            (this.isStable = !0),
            (this.onUnstable = new Q()),
            (this.onMicrotaskEmpty = new Q()),
            (this.onStable = new Q()),
            (this.onError = new Q());
        }
        run(e, t, i) {
          return e.apply(t, i);
        }
        runGuarded(e, t, i) {
          return e.apply(t, i);
        }
        runOutsideAngular(e) {
          return e();
        }
        runTask(e, t, i, r) {
          return e.apply(t, i);
        }
      }
      let nh = (() => {
          class n {
            constructor(t) {
              (this._ngZone = t),
                (this._pendingCount = 0),
                (this._isZoneStable = !0),
                (this._didWork = !1),
                (this._callbacks = []),
                (this.taskTrackingZone = null),
                this._watchAngularEvents(),
                t.run(() => {
                  this.taskTrackingZone =
                    "undefined" == typeof Zone
                      ? null
                      : Zone.current.get("TaskTrackingZone");
                });
            }
            _watchAngularEvents() {
              this._ngZone.onUnstable.subscribe({
                next: () => {
                  (this._didWork = !0), (this._isZoneStable = !1);
                },
              }),
                this._ngZone.runOutsideAngular(() => {
                  this._ngZone.onStable.subscribe({
                    next: () => {
                      ee.assertNotInAngularZone(),
                        Jd(() => {
                          (this._isZoneStable = !0),
                            this._runCallbacksIfReady();
                        });
                    },
                  });
                });
            }
            increasePendingRequestCount() {
              return (
                (this._pendingCount += 1),
                (this._didWork = !0),
                this._pendingCount
              );
            }
            decreasePendingRequestCount() {
              if (((this._pendingCount -= 1), this._pendingCount < 0))
                throw new Error("pending async requests below zero");
              return this._runCallbacksIfReady(), this._pendingCount;
            }
            isStable() {
              return (
                this._isZoneStable &&
                0 === this._pendingCount &&
                !this._ngZone.hasPendingMacrotasks
              );
            }
            _runCallbacksIfReady() {
              if (this.isStable())
                Jd(() => {
                  for (; 0 !== this._callbacks.length; ) {
                    let t = this._callbacks.pop();
                    clearTimeout(t.timeoutId), t.doneCb(this._didWork);
                  }
                  this._didWork = !1;
                });
              else {
                let t = this.getPendingTasks();
                (this._callbacks = this._callbacks.filter(
                  (i) =>
                    !i.updateCb ||
                    !i.updateCb(t) ||
                    (clearTimeout(i.timeoutId), !1)
                )),
                  (this._didWork = !0);
              }
            }
            getPendingTasks() {
              return this.taskTrackingZone
                ? this.taskTrackingZone.macroTasks.map((t) => ({
                    source: t.source,
                    creationLocation: t.creationLocation,
                    data: t.data,
                  }))
                : [];
            }
            addCallback(t, i, r) {
              let s = -1;
              i &&
                i > 0 &&
                (s = setTimeout(() => {
                  (this._callbacks = this._callbacks.filter(
                    (o) => o.timeoutId !== s
                  )),
                    t(this._didWork, this.getPendingTasks());
                }, i)),
                this._callbacks.push({ doneCb: t, timeoutId: s, updateCb: r });
            }
            whenStable(t, i, r) {
              if (r && !this.taskTrackingZone)
                throw new Error(
                  'Task tracking zone is required when passing an update callback to whenStable(). Is "zone.js/plugins/task-tracking" loaded?'
                );
              this.addCallback(t, i, r), this._runCallbacksIfReady();
            }
            getPendingRequestCount() {
              return this._pendingCount;
            }
            findProviders(t, i, r) {
              return [];
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(ee));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })(),
        gb = (() => {
          class n {
            constructor() {
              (this._applications = new Map()), ih.addToWindow(this);
            }
            registerApplication(t, i) {
              this._applications.set(t, i);
            }
            unregisterApplication(t) {
              this._applications.delete(t);
            }
            unregisterAllApplications() {
              this._applications.clear();
            }
            getTestability(t) {
              return this._applications.get(t) || null;
            }
            getAllTestabilities() {
              return Array.from(this._applications.values());
            }
            getAllRootElements() {
              return Array.from(this._applications.keys());
            }
            findTestabilityInTree(t, i = !0) {
              return ih.findTestabilityInTree(this, t, i);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })();
      class _F {
        addToWindow(e) {}
        findTestabilityInTree(e, t, i) {
          return null;
        }
      }
      let mn,
        ih = new _F();
      const mb = new T("AllowMultipleToken");
      class _b {
        constructor(e, t) {
          (this.name = e), (this.token = t);
        }
      }
      function yb(n, e, t = []) {
        const i = `Platform: ${e}`,
          r = new T(i);
        return (s = []) => {
          let o = vb();
          if (!o || o.injector.get(mb, !1))
            if (n) n(t.concat(s).concat({ provide: r, useValue: !0 }));
            else {
              const a = t
                .concat(s)
                .concat(
                  { provide: r, useValue: !0 },
                  { provide: fd, useValue: "platform" }
                );
              !(function CF(n) {
                if (mn && !mn.destroyed && !mn.injector.get(mb, !1))
                  throw new ne(400, "");
                mn = n.get(bb);
                const e = n.get(cb, null);
                e && e.forEach((t) => t());
              })(Qe.create({ providers: a, name: i }));
            }
          return (function wF(n) {
            const e = vb();
            if (!e) throw new ne(401, "");
            return e;
          })();
        };
      }
      function vb() {
        return mn && !mn.destroyed ? mn : null;
      }
      let bb = (() => {
        class n {
          constructor(t) {
            (this._injector = t),
              (this._modules = []),
              (this._destroyListeners = []),
              (this._destroyed = !1);
          }
          bootstrapModuleFactory(t, i) {
            const a = (function DF(n, e) {
                let t;
                return (
                  (t =
                    "noop" === n
                      ? new mF()
                      : ("zone.js" === n ? void 0 : n) ||
                        new ee({
                          enableLongStackTrace: !1,
                          shouldCoalesceEventChangeDetection: !!(null == e
                            ? void 0
                            : e.ngZoneEventCoalescing),
                          shouldCoalesceRunChangeDetection: !!(null == e
                            ? void 0
                            : e.ngZoneRunCoalescing),
                        })),
                  t
                );
              })(i ? i.ngZone : void 0, {
                ngZoneEventCoalescing: (i && i.ngZoneEventCoalescing) || !1,
                ngZoneRunCoalescing: (i && i.ngZoneRunCoalescing) || !1,
              }),
              l = [{ provide: ee, useValue: a }];
            return a.run(() => {
              const c = Qe.create({
                  providers: l,
                  parent: this.injector,
                  name: t.moduleType.name,
                }),
                u = t.create(c),
                d = u.injector.get(Tr, null);
              if (!d) throw new ne(402, "");
              return (
                a.runOutsideAngular(() => {
                  const h = a.onError.subscribe({
                    next: (f) => {
                      d.handleError(f);
                    },
                  });
                  u.onDestroy(() => {
                    rh(this._modules, u), h.unsubscribe();
                  });
                }),
                (function EF(n, e, t) {
                  try {
                    const i = t();
                    return Js(i)
                      ? i.catch((r) => {
                          throw (
                            (e.runOutsideAngular(() => n.handleError(r)), r)
                          );
                        })
                      : i;
                  } catch (i) {
                    throw (e.runOutsideAngular(() => n.handleError(i)), i);
                  }
                })(d, a, () => {
                  const h = u.injector.get(Jr);
                  return (
                    h.runInitializers(),
                    h.donePromise.then(
                      () => (
                        (function ex(n) {
                          Tt(n, "Expected localeId to be defined"),
                            "string" == typeof n &&
                              (tv = n.toLowerCase().replace(/_/g, "-"));
                        })(u.injector.get(Qn, Ka) || Ka),
                        this._moduleDoBootstrap(u),
                        u
                      )
                    )
                  );
                })
              );
            });
          }
          bootstrapModule(t, i = []) {
            const r = Cb({}, i);
            return (function vF(n, e, t) {
              const i = new Bd(t);
              return Promise.resolve(i);
            })(0, 0, t).then((s) => this.bootstrapModuleFactory(s, r));
          }
          _moduleDoBootstrap(t) {
            const i = t.injector.get(es);
            if (t._bootstrapComponents.length > 0)
              t._bootstrapComponents.forEach((r) => i.bootstrap(r));
            else {
              if (!t.instance.ngDoBootstrap) throw new ne(403, "");
              t.instance.ngDoBootstrap(i);
            }
            this._modules.push(t);
          }
          onDestroy(t) {
            this._destroyListeners.push(t);
          }
          get injector() {
            return this._injector;
          }
          destroy() {
            if (this._destroyed) throw new ne(404, "");
            this._modules.slice().forEach((t) => t.destroy()),
              this._destroyListeners.forEach((t) => t()),
              (this._destroyed = !0);
          }
          get destroyed() {
            return this._destroyed;
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(Qe));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      function Cb(n, e) {
        return Array.isArray(e)
          ? e.reduce(Cb, n)
          : Object.assign(Object.assign({}, n), e);
      }
      let es = (() => {
        class n {
          constructor(t, i, r, s, o) {
            (this._zone = t),
              (this._injector = i),
              (this._exceptionHandler = r),
              (this._componentFactoryResolver = s),
              (this._initStatus = o),
              (this._bootstrapListeners = []),
              (this._views = []),
              (this._runningTick = !1),
              (this._stable = !0),
              (this.componentTypes = []),
              (this.components = []),
              (this._onMicrotaskEmptySubscription =
                this._zone.onMicrotaskEmpty.subscribe({
                  next: () => {
                    this._zone.run(() => {
                      this.tick();
                    });
                  },
                }));
            const a = new fe((c) => {
                (this._stable =
                  this._zone.isStable &&
                  !this._zone.hasPendingMacrotasks &&
                  !this._zone.hasPendingMicrotasks),
                  this._zone.runOutsideAngular(() => {
                    c.next(this._stable), c.complete();
                  });
              }),
              l = new fe((c) => {
                let u;
                this._zone.runOutsideAngular(() => {
                  u = this._zone.onStable.subscribe(() => {
                    ee.assertNotInAngularZone(),
                      Jd(() => {
                        !this._stable &&
                          !this._zone.hasPendingMacrotasks &&
                          !this._zone.hasPendingMicrotasks &&
                          ((this._stable = !0), c.next(!0));
                      });
                  });
                });
                const d = this._zone.onUnstable.subscribe(() => {
                  ee.assertInAngularZone(),
                    this._stable &&
                      ((this._stable = !1),
                      this._zone.runOutsideAngular(() => {
                        c.next(!1);
                      }));
                });
                return () => {
                  u.unsubscribe(), d.unsubscribe();
                };
              });
            this.isStable = lr(
              a,
              l.pipe(
                (function S0(n = {}) {
                  const {
                    connector: e = () => new le(),
                    resetOnError: t = !0,
                    resetOnComplete: i = !0,
                    resetOnRefCountZero: r = !0,
                  } = n;
                  return (s) => {
                    let o = null,
                      a = null,
                      l = null,
                      c = 0,
                      u = !1,
                      d = !1;
                    const h = () => {
                        null == a || a.unsubscribe(), (a = null);
                      },
                      f = () => {
                        h(), (o = l = null), (u = d = !1);
                      },
                      p = () => {
                        const g = o;
                        f(), null == g || g.unsubscribe();
                      };
                    return Fe((g, y) => {
                      c++, !d && !u && h();
                      const v = (l = null != l ? l : e());
                      y.add(() => {
                        c--, 0 === c && !d && !u && (a = Bc(p, r));
                      }),
                        v.subscribe(y),
                        o ||
                          ((o = new kc({
                            next: (m) => v.next(m),
                            error: (m) => {
                              (d = !0), h(), (a = Bc(f, t, m)), v.error(m);
                            },
                            complete: () => {
                              (u = !0), h(), (a = Bc(f, i)), v.complete();
                            },
                          })),
                          et(g).subscribe(o));
                    })(s);
                  };
                })()
              )
            );
          }
          bootstrap(t, i) {
            if (!this._initStatus.done) throw new ne(405, "");
            let r;
            (r =
              t instanceof Sv
                ? t
                : this._componentFactoryResolver.resolveComponentFactory(t)),
              this.componentTypes.push(r.componentType);
            const s = (function bF(n) {
                return n.isBoundToModule;
              })(r)
                ? void 0
                : this._injector.get(Zn),
              a = r.create(Qe.NULL, [], i || r.selector, s),
              l = a.location.nativeElement,
              c = a.injector.get(nh, null),
              u = c && a.injector.get(gb);
            return (
              c && u && u.registerApplication(l, c),
              a.onDestroy(() => {
                this.detachView(a.hostView),
                  rh(this.components, a),
                  u && u.unregisterApplication(l);
              }),
              this._loadComponent(a),
              a
            );
          }
          tick() {
            if (this._runningTick) throw new ne(101, "");
            try {
              this._runningTick = !0;
              for (let t of this._views) t.detectChanges();
            } catch (t) {
              this._zone.runOutsideAngular(() =>
                this._exceptionHandler.handleError(t)
              );
            } finally {
              this._runningTick = !1;
            }
          }
          attachView(t) {
            const i = t;
            this._views.push(i), i.attachToAppRef(this);
          }
          detachView(t) {
            const i = t;
            rh(this._views, i), i.detachFromAppRef();
          }
          _loadComponent(t) {
            this.attachView(t.hostView),
              this.tick(),
              this.components.push(t),
              this._injector
                .get(ub, [])
                .concat(this._bootstrapListeners)
                .forEach((r) => r(t));
          }
          ngOnDestroy() {
            this._views.slice().forEach((t) => t.destroy()),
              this._onMicrotaskEmptySubscription.unsubscribe();
          }
          get viewCount() {
            return this._views.length;
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(ee), b(Qe), b(Tr), b($i), b(Jr));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      function rh(n, e) {
        const t = n.indexOf(e);
        t > -1 && n.splice(t, 1);
      }
      let Db = !0,
        vi = (() => {
          class n {}
          return (n.__NG_ELEMENT_ID__ = AF), n;
        })();
      function AF(n) {
        return (function TF(n, e, t) {
          if (aa(n) && !t) {
            const i = It(n.index, e);
            return new lo(i, i);
          }
          return 47 & n.type ? new lo(e[16], e) : null;
        })(Ye(), C(), 16 == (16 & n));
      }
      class Ib {
        constructor() {}
        supports(e) {
          return Qs(e);
        }
        create(e) {
          return new RF(e);
        }
      }
      const FF = (n, e) => e;
      class RF {
        constructor(e) {
          (this.length = 0),
            (this._linkedRecords = null),
            (this._unlinkedRecords = null),
            (this._previousItHead = null),
            (this._itHead = null),
            (this._itTail = null),
            (this._additionsHead = null),
            (this._additionsTail = null),
            (this._movesHead = null),
            (this._movesTail = null),
            (this._removalsHead = null),
            (this._removalsTail = null),
            (this._identityChangesHead = null),
            (this._identityChangesTail = null),
            (this._trackByFn = e || FF);
        }
        forEachItem(e) {
          let t;
          for (t = this._itHead; null !== t; t = t._next) e(t);
        }
        forEachOperation(e) {
          let t = this._itHead,
            i = this._removalsHead,
            r = 0,
            s = null;
          for (; t || i; ) {
            const o = !i || (t && t.currentIndex < kb(i, r, s)) ? t : i,
              a = kb(o, r, s),
              l = o.currentIndex;
            if (o === i) r--, (i = i._nextRemoved);
            else if (((t = t._next), null == o.previousIndex)) r++;
            else {
              s || (s = []);
              const c = a - r,
                u = l - r;
              if (c != u) {
                for (let h = 0; h < c; h++) {
                  const f = h < s.length ? s[h] : (s[h] = 0),
                    p = f + h;
                  u <= p && p < c && (s[h] = f + 1);
                }
                s[o.previousIndex] = u - c;
              }
            }
            a !== l && e(o, a, l);
          }
        }
        forEachPreviousItem(e) {
          let t;
          for (t = this._previousItHead; null !== t; t = t._nextPrevious) e(t);
        }
        forEachAddedItem(e) {
          let t;
          for (t = this._additionsHead; null !== t; t = t._nextAdded) e(t);
        }
        forEachMovedItem(e) {
          let t;
          for (t = this._movesHead; null !== t; t = t._nextMoved) e(t);
        }
        forEachRemovedItem(e) {
          let t;
          for (t = this._removalsHead; null !== t; t = t._nextRemoved) e(t);
        }
        forEachIdentityChange(e) {
          let t;
          for (
            t = this._identityChangesHead;
            null !== t;
            t = t._nextIdentityChange
          )
            e(t);
        }
        diff(e) {
          if ((null == e && (e = []), !Qs(e))) throw new ne(900, "");
          return this.check(e) ? this : null;
        }
        onDestroy() {}
        check(e) {
          this._reset();
          let r,
            s,
            o,
            t = this._itHead,
            i = !1;
          if (Array.isArray(e)) {
            this.length = e.length;
            for (let a = 0; a < this.length; a++)
              (s = e[a]),
                (o = this._trackByFn(a, s)),
                null !== t && Object.is(t.trackById, o)
                  ? (i && (t = this._verifyReinsertion(t, s, o, a)),
                    Object.is(t.item, s) || this._addIdentityChange(t, s))
                  : ((t = this._mismatch(t, s, o, a)), (i = !0)),
                (t = t._next);
          } else
            (r = 0),
              (function jO(n, e) {
                if (Array.isArray(n))
                  for (let t = 0; t < n.length; t++) e(n[t]);
                else {
                  const t = n[Nr()]();
                  let i;
                  for (; !(i = t.next()).done; ) e(i.value);
                }
              })(e, (a) => {
                (o = this._trackByFn(r, a)),
                  null !== t && Object.is(t.trackById, o)
                    ? (i && (t = this._verifyReinsertion(t, a, o, r)),
                      Object.is(t.item, a) || this._addIdentityChange(t, a))
                    : ((t = this._mismatch(t, a, o, r)), (i = !0)),
                  (t = t._next),
                  r++;
              }),
              (this.length = r);
          return this._truncate(t), (this.collection = e), this.isDirty;
        }
        get isDirty() {
          return (
            null !== this._additionsHead ||
            null !== this._movesHead ||
            null !== this._removalsHead ||
            null !== this._identityChangesHead
          );
        }
        _reset() {
          if (this.isDirty) {
            let e;
            for (
              e = this._previousItHead = this._itHead;
              null !== e;
              e = e._next
            )
              e._nextPrevious = e._next;
            for (e = this._additionsHead; null !== e; e = e._nextAdded)
              e.previousIndex = e.currentIndex;
            for (
              this._additionsHead = this._additionsTail = null,
                e = this._movesHead;
              null !== e;
              e = e._nextMoved
            )
              e.previousIndex = e.currentIndex;
            (this._movesHead = this._movesTail = null),
              (this._removalsHead = this._removalsTail = null),
              (this._identityChangesHead = this._identityChangesTail = null);
          }
        }
        _mismatch(e, t, i, r) {
          let s;
          return (
            null === e ? (s = this._itTail) : ((s = e._prev), this._remove(e)),
            null !==
            (e =
              null === this._unlinkedRecords
                ? null
                : this._unlinkedRecords.get(i, null))
              ? (Object.is(e.item, t) || this._addIdentityChange(e, t),
                this._reinsertAfter(e, s, r))
              : null !==
                (e =
                  null === this._linkedRecords
                    ? null
                    : this._linkedRecords.get(i, r))
              ? (Object.is(e.item, t) || this._addIdentityChange(e, t),
                this._moveAfter(e, s, r))
              : (e = this._addAfter(new PF(t, i), s, r)),
            e
          );
        }
        _verifyReinsertion(e, t, i, r) {
          let s =
            null === this._unlinkedRecords
              ? null
              : this._unlinkedRecords.get(i, null);
          return (
            null !== s
              ? (e = this._reinsertAfter(s, e._prev, r))
              : e.currentIndex != r &&
                ((e.currentIndex = r), this._addToMoves(e, r)),
            e
          );
        }
        _truncate(e) {
          for (; null !== e; ) {
            const t = e._next;
            this._addToRemovals(this._unlink(e)), (e = t);
          }
          null !== this._unlinkedRecords && this._unlinkedRecords.clear(),
            null !== this._additionsTail &&
              (this._additionsTail._nextAdded = null),
            null !== this._movesTail && (this._movesTail._nextMoved = null),
            null !== this._itTail && (this._itTail._next = null),
            null !== this._removalsTail &&
              (this._removalsTail._nextRemoved = null),
            null !== this._identityChangesTail &&
              (this._identityChangesTail._nextIdentityChange = null);
        }
        _reinsertAfter(e, t, i) {
          null !== this._unlinkedRecords && this._unlinkedRecords.remove(e);
          const r = e._prevRemoved,
            s = e._nextRemoved;
          return (
            null === r ? (this._removalsHead = s) : (r._nextRemoved = s),
            null === s ? (this._removalsTail = r) : (s._prevRemoved = r),
            this._insertAfter(e, t, i),
            this._addToMoves(e, i),
            e
          );
        }
        _moveAfter(e, t, i) {
          return (
            this._unlink(e),
            this._insertAfter(e, t, i),
            this._addToMoves(e, i),
            e
          );
        }
        _addAfter(e, t, i) {
          return (
            this._insertAfter(e, t, i),
            (this._additionsTail =
              null === this._additionsTail
                ? (this._additionsHead = e)
                : (this._additionsTail._nextAdded = e)),
            e
          );
        }
        _insertAfter(e, t, i) {
          const r = null === t ? this._itHead : t._next;
          return (
            (e._next = r),
            (e._prev = t),
            null === r ? (this._itTail = e) : (r._prev = e),
            null === t ? (this._itHead = e) : (t._next = e),
            null === this._linkedRecords && (this._linkedRecords = new xb()),
            this._linkedRecords.put(e),
            (e.currentIndex = i),
            e
          );
        }
        _remove(e) {
          return this._addToRemovals(this._unlink(e));
        }
        _unlink(e) {
          null !== this._linkedRecords && this._linkedRecords.remove(e);
          const t = e._prev,
            i = e._next;
          return (
            null === t ? (this._itHead = i) : (t._next = i),
            null === i ? (this._itTail = t) : (i._prev = t),
            e
          );
        }
        _addToMoves(e, t) {
          return (
            e.previousIndex === t ||
              (this._movesTail =
                null === this._movesTail
                  ? (this._movesHead = e)
                  : (this._movesTail._nextMoved = e)),
            e
          );
        }
        _addToRemovals(e) {
          return (
            null === this._unlinkedRecords &&
              (this._unlinkedRecords = new xb()),
            this._unlinkedRecords.put(e),
            (e.currentIndex = null),
            (e._nextRemoved = null),
            null === this._removalsTail
              ? ((this._removalsTail = this._removalsHead = e),
                (e._prevRemoved = null))
              : ((e._prevRemoved = this._removalsTail),
                (this._removalsTail = this._removalsTail._nextRemoved = e)),
            e
          );
        }
        _addIdentityChange(e, t) {
          return (
            (e.item = t),
            (this._identityChangesTail =
              null === this._identityChangesTail
                ? (this._identityChangesHead = e)
                : (this._identityChangesTail._nextIdentityChange = e)),
            e
          );
        }
      }
      class PF {
        constructor(e, t) {
          (this.item = e),
            (this.trackById = t),
            (this.currentIndex = null),
            (this.previousIndex = null),
            (this._nextPrevious = null),
            (this._prev = null),
            (this._next = null),
            (this._prevDup = null),
            (this._nextDup = null),
            (this._prevRemoved = null),
            (this._nextRemoved = null),
            (this._nextAdded = null),
            (this._nextMoved = null),
            (this._nextIdentityChange = null);
        }
      }
      class NF {
        constructor() {
          (this._head = null), (this._tail = null);
        }
        add(e) {
          null === this._head
            ? ((this._head = this._tail = e),
              (e._nextDup = null),
              (e._prevDup = null))
            : ((this._tail._nextDup = e),
              (e._prevDup = this._tail),
              (e._nextDup = null),
              (this._tail = e));
        }
        get(e, t) {
          let i;
          for (i = this._head; null !== i; i = i._nextDup)
            if (
              (null === t || t <= i.currentIndex) &&
              Object.is(i.trackById, e)
            )
              return i;
          return null;
        }
        remove(e) {
          const t = e._prevDup,
            i = e._nextDup;
          return (
            null === t ? (this._head = i) : (t._nextDup = i),
            null === i ? (this._tail = t) : (i._prevDup = t),
            null === this._head
          );
        }
      }
      class xb {
        constructor() {
          this.map = new Map();
        }
        put(e) {
          const t = e.trackById;
          let i = this.map.get(t);
          i || ((i = new NF()), this.map.set(t, i)), i.add(e);
        }
        get(e, t) {
          const r = this.map.get(e);
          return r ? r.get(e, t) : null;
        }
        remove(e) {
          const t = e.trackById;
          return this.map.get(t).remove(e) && this.map.delete(t), e;
        }
        get isEmpty() {
          return 0 === this.map.size;
        }
        clear() {
          this.map.clear();
        }
      }
      function kb(n, e, t) {
        const i = n.previousIndex;
        if (null === i) return i;
        let r = 0;
        return t && i < t.length && (r = t[i]), i + e + r;
      }
      class Fb {
        constructor() {}
        supports(e) {
          return e instanceof Map || vd(e);
        }
        create() {
          return new LF();
        }
      }
      class LF {
        constructor() {
          (this._records = new Map()),
            (this._mapHead = null),
            (this._appendAfter = null),
            (this._previousMapHead = null),
            (this._changesHead = null),
            (this._changesTail = null),
            (this._additionsHead = null),
            (this._additionsTail = null),
            (this._removalsHead = null),
            (this._removalsTail = null);
        }
        get isDirty() {
          return (
            null !== this._additionsHead ||
            null !== this._changesHead ||
            null !== this._removalsHead
          );
        }
        forEachItem(e) {
          let t;
          for (t = this._mapHead; null !== t; t = t._next) e(t);
        }
        forEachPreviousItem(e) {
          let t;
          for (t = this._previousMapHead; null !== t; t = t._nextPrevious) e(t);
        }
        forEachChangedItem(e) {
          let t;
          for (t = this._changesHead; null !== t; t = t._nextChanged) e(t);
        }
        forEachAddedItem(e) {
          let t;
          for (t = this._additionsHead; null !== t; t = t._nextAdded) e(t);
        }
        forEachRemovedItem(e) {
          let t;
          for (t = this._removalsHead; null !== t; t = t._nextRemoved) e(t);
        }
        diff(e) {
          if (e) {
            if (!(e instanceof Map || vd(e))) throw new ne(900, "");
          } else e = new Map();
          return this.check(e) ? this : null;
        }
        onDestroy() {}
        check(e) {
          this._reset();
          let t = this._mapHead;
          if (
            ((this._appendAfter = null),
            this._forEach(e, (i, r) => {
              if (t && t.key === r)
                this._maybeAddToChanges(t, i),
                  (this._appendAfter = t),
                  (t = t._next);
              else {
                const s = this._getOrCreateRecordForKey(r, i);
                t = this._insertBeforeOrAppend(t, s);
              }
            }),
            t)
          ) {
            t._prev && (t._prev._next = null), (this._removalsHead = t);
            for (let i = t; null !== i; i = i._nextRemoved)
              i === this._mapHead && (this._mapHead = null),
                this._records.delete(i.key),
                (i._nextRemoved = i._next),
                (i.previousValue = i.currentValue),
                (i.currentValue = null),
                (i._prev = null),
                (i._next = null);
          }
          return (
            this._changesTail && (this._changesTail._nextChanged = null),
            this._additionsTail && (this._additionsTail._nextAdded = null),
            this.isDirty
          );
        }
        _insertBeforeOrAppend(e, t) {
          if (e) {
            const i = e._prev;
            return (
              (t._next = e),
              (t._prev = i),
              (e._prev = t),
              i && (i._next = t),
              e === this._mapHead && (this._mapHead = t),
              (this._appendAfter = e),
              e
            );
          }
          return (
            this._appendAfter
              ? ((this._appendAfter._next = t), (t._prev = this._appendAfter))
              : (this._mapHead = t),
            (this._appendAfter = t),
            null
          );
        }
        _getOrCreateRecordForKey(e, t) {
          if (this._records.has(e)) {
            const r = this._records.get(e);
            this._maybeAddToChanges(r, t);
            const s = r._prev,
              o = r._next;
            return (
              s && (s._next = o),
              o && (o._prev = s),
              (r._next = null),
              (r._prev = null),
              r
            );
          }
          const i = new VF(e);
          return (
            this._records.set(e, i),
            (i.currentValue = t),
            this._addToAdditions(i),
            i
          );
        }
        _reset() {
          if (this.isDirty) {
            let e;
            for (
              this._previousMapHead = this._mapHead, e = this._previousMapHead;
              null !== e;
              e = e._next
            )
              e._nextPrevious = e._next;
            for (e = this._changesHead; null !== e; e = e._nextChanged)
              e.previousValue = e.currentValue;
            for (e = this._additionsHead; null != e; e = e._nextAdded)
              e.previousValue = e.currentValue;
            (this._changesHead = this._changesTail = null),
              (this._additionsHead = this._additionsTail = null),
              (this._removalsHead = null);
          }
        }
        _maybeAddToChanges(e, t) {
          Object.is(t, e.currentValue) ||
            ((e.previousValue = e.currentValue),
            (e.currentValue = t),
            this._addToChanges(e));
        }
        _addToAdditions(e) {
          null === this._additionsHead
            ? (this._additionsHead = this._additionsTail = e)
            : ((this._additionsTail._nextAdded = e), (this._additionsTail = e));
        }
        _addToChanges(e) {
          null === this._changesHead
            ? (this._changesHead = this._changesTail = e)
            : ((this._changesTail._nextChanged = e), (this._changesTail = e));
        }
        _forEach(e, t) {
          e instanceof Map
            ? e.forEach(t)
            : Object.keys(e).forEach((i) => t(e[i], i));
        }
      }
      class VF {
        constructor(e) {
          (this.key = e),
            (this.previousValue = null),
            (this.currentValue = null),
            (this._nextPrevious = null),
            (this._next = null),
            (this._prev = null),
            (this._nextAdded = null),
            (this._nextRemoved = null),
            (this._nextChanged = null);
        }
      }
      function Rb() {
        return new mo([new Ib()]);
      }
      let mo = (() => {
        class n {
          constructor(t) {
            this.factories = t;
          }
          static create(t, i) {
            if (null != i) {
              const r = i.factories.slice();
              t = t.concat(r);
            }
            return new n(t);
          }
          static extend(t) {
            return {
              provide: n,
              useFactory: (i) => n.create(t, i || Rb()),
              deps: [[n, new Er(), new An()]],
            };
          }
          find(t) {
            const i = this.factories.find((r) => r.supports(t));
            if (null != i) return i;
            throw new ne(901, "");
          }
        }
        return (n.ɵprov = I({ token: n, providedIn: "root", factory: Rb })), n;
      })();
      function Pb() {
        return new ts([new Fb()]);
      }
      let ts = (() => {
        class n {
          constructor(t) {
            this.factories = t;
          }
          static create(t, i) {
            if (i) {
              const r = i.factories.slice();
              t = t.concat(r);
            }
            return new n(t);
          }
          static extend(t) {
            return {
              provide: n,
              useFactory: (i) => n.create(t, i || Pb()),
              deps: [[n, new Er(), new An()]],
            };
          }
          find(t) {
            const i = this.factories.find((s) => s.supports(t));
            if (i) return i;
            throw new ne(901, "");
          }
        }
        return (n.ɵprov = I({ token: n, providedIn: "root", factory: Pb })), n;
      })();
      const BF = [new Fb()],
        HF = new mo([new Ib()]),
        UF = new ts(BF),
        $F = yb(null, "core", [
          { provide: go, useValue: "unknown" },
          { provide: bb, deps: [Qe] },
          { provide: gb, deps: [] },
          { provide: db, deps: [] },
        ]),
        KF = [
          { provide: es, useClass: es, deps: [ee, Qe, Tr, $i, Jr] },
          {
            provide: ok,
            deps: [ee],
            useFactory: function YF(n) {
              let e = [];
              return (
                n.onStable.subscribe(() => {
                  for (; e.length; ) e.pop()();
                }),
                function (t) {
                  e.push(t);
                }
              );
            },
          },
          { provide: Jr, useClass: Jr, deps: [[new An(), rl]] },
          { provide: sl, useClass: sl, deps: [] },
          lF,
          {
            provide: mo,
            useFactory: function zF() {
              return HF;
            },
            deps: [],
          },
          {
            provide: ts,
            useFactory: function GF() {
              return UF;
            },
            deps: [],
          },
          {
            provide: Qn,
            useFactory: function qF(n) {
              return (
                n ||
                (function WF() {
                  return (
                    ("undefined" != typeof $localize && $localize.locale) || Ka
                  );
                })()
              );
            },
            deps: [[new js(Qn), new An(), new Er()]],
          },
          { provide: hb, useValue: "USD" },
        ];
      let ZF = (() => {
          class n {
            constructor(t) {}
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(es));
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({ providers: KF })),
            n
          );
        })(),
        al = null;
      function Pn() {
        return al;
      }
      const ue = new T("DocumentToken");
      let qi = (() => {
        class n {
          historyGo(t) {
            throw new Error("Not implemented");
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵprov = I({
            token: n,
            factory: function () {
              return (function eR() {
                return b(Nb);
              })();
            },
            providedIn: "platform",
          })),
          n
        );
      })();
      const tR = new T("Location Initialized");
      let Nb = (() => {
        class n extends qi {
          constructor(t) {
            super(), (this._doc = t), this._init();
          }
          _init() {
            (this.location = window.location), (this._history = window.history);
          }
          getBaseHrefFromDOM() {
            return Pn().getBaseHref(this._doc);
          }
          onPopState(t) {
            const i = Pn().getGlobalEventTarget(this._doc, "window");
            return (
              i.addEventListener("popstate", t, !1),
              () => i.removeEventListener("popstate", t)
            );
          }
          onHashChange(t) {
            const i = Pn().getGlobalEventTarget(this._doc, "window");
            return (
              i.addEventListener("hashchange", t, !1),
              () => i.removeEventListener("hashchange", t)
            );
          }
          get href() {
            return this.location.href;
          }
          get protocol() {
            return this.location.protocol;
          }
          get hostname() {
            return this.location.hostname;
          }
          get port() {
            return this.location.port;
          }
          get pathname() {
            return this.location.pathname;
          }
          get search() {
            return this.location.search;
          }
          get hash() {
            return this.location.hash;
          }
          set pathname(t) {
            this.location.pathname = t;
          }
          pushState(t, i, r) {
            Lb() ? this._history.pushState(t, i, r) : (this.location.hash = r);
          }
          replaceState(t, i, r) {
            Lb()
              ? this._history.replaceState(t, i, r)
              : (this.location.hash = r);
          }
          forward() {
            this._history.forward();
          }
          back() {
            this._history.back();
          }
          historyGo(t = 0) {
            this._history.go(t);
          }
          getState() {
            return this._history.state;
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(ue));
          }),
          (n.ɵprov = I({
            token: n,
            factory: function () {
              return (function nR() {
                return new Nb(b(ue));
              })();
            },
            providedIn: "platform",
          })),
          n
        );
      })();
      function Lb() {
        return !!window.history.pushState;
      }
      function ch(n, e) {
        if (0 == n.length) return e;
        if (0 == e.length) return n;
        let t = 0;
        return (
          n.endsWith("/") && t++,
          e.startsWith("/") && t++,
          2 == t ? n + e.substring(1) : 1 == t ? n + e : n + "/" + e
        );
      }
      function Vb(n) {
        const e = n.match(/#|\?|$/),
          t = (e && e.index) || n.length;
        return n.slice(0, t - ("/" === n[t - 1] ? 1 : 0)) + n.slice(t);
      }
      function Xn(n) {
        return n && "?" !== n[0] ? "?" + n : n;
      }
      let ns = (() => {
        class n {
          historyGo(t) {
            throw new Error("Not implemented");
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵprov = I({
            token: n,
            factory: function () {
              return (function iR(n) {
                const e = b(ue).location;
                return new Bb(b(qi), (e && e.origin) || "");
              })();
            },
            providedIn: "root",
          })),
          n
        );
      })();
      const uh = new T("appBaseHref");
      let Bb = (() => {
          class n extends ns {
            constructor(t, i) {
              if (
                (super(),
                (this._platformLocation = t),
                (this._removeListenerFns = []),
                null == i && (i = this._platformLocation.getBaseHrefFromDOM()),
                null == i)
              )
                throw new Error(
                  "No base href set. Please provide a value for the APP_BASE_HREF token or add a base element to the document."
                );
              this._baseHref = i;
            }
            ngOnDestroy() {
              for (; this._removeListenerFns.length; )
                this._removeListenerFns.pop()();
            }
            onPopState(t) {
              this._removeListenerFns.push(
                this._platformLocation.onPopState(t),
                this._platformLocation.onHashChange(t)
              );
            }
            getBaseHref() {
              return this._baseHref;
            }
            prepareExternalUrl(t) {
              return ch(this._baseHref, t);
            }
            path(t = !1) {
              const i =
                  this._platformLocation.pathname +
                  Xn(this._platformLocation.search),
                r = this._platformLocation.hash;
              return r && t ? `${i}${r}` : i;
            }
            pushState(t, i, r, s) {
              const o = this.prepareExternalUrl(r + Xn(s));
              this._platformLocation.pushState(t, i, o);
            }
            replaceState(t, i, r, s) {
              const o = this.prepareExternalUrl(r + Xn(s));
              this._platformLocation.replaceState(t, i, o);
            }
            forward() {
              this._platformLocation.forward();
            }
            back() {
              this._platformLocation.back();
            }
            historyGo(t = 0) {
              var i, r;
              null === (r = (i = this._platformLocation).historyGo) ||
                void 0 === r ||
                r.call(i, t);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(qi), b(uh, 8));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })(),
        rR = (() => {
          class n extends ns {
            constructor(t, i) {
              super(),
                (this._platformLocation = t),
                (this._baseHref = ""),
                (this._removeListenerFns = []),
                null != i && (this._baseHref = i);
            }
            ngOnDestroy() {
              for (; this._removeListenerFns.length; )
                this._removeListenerFns.pop()();
            }
            onPopState(t) {
              this._removeListenerFns.push(
                this._platformLocation.onPopState(t),
                this._platformLocation.onHashChange(t)
              );
            }
            getBaseHref() {
              return this._baseHref;
            }
            path(t = !1) {
              let i = this._platformLocation.hash;
              return null == i && (i = "#"), i.length > 0 ? i.substring(1) : i;
            }
            prepareExternalUrl(t) {
              const i = ch(this._baseHref, t);
              return i.length > 0 ? "#" + i : i;
            }
            pushState(t, i, r, s) {
              let o = this.prepareExternalUrl(r + Xn(s));
              0 == o.length && (o = this._platformLocation.pathname),
                this._platformLocation.pushState(t, i, o);
            }
            replaceState(t, i, r, s) {
              let o = this.prepareExternalUrl(r + Xn(s));
              0 == o.length && (o = this._platformLocation.pathname),
                this._platformLocation.replaceState(t, i, o);
            }
            forward() {
              this._platformLocation.forward();
            }
            back() {
              this._platformLocation.back();
            }
            historyGo(t = 0) {
              var i, r;
              null === (r = (i = this._platformLocation).historyGo) ||
                void 0 === r ||
                r.call(i, t);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(qi), b(uh, 8));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })(),
        ll = (() => {
          class n {
            constructor(t, i) {
              (this._subject = new Q()),
                (this._urlChangeListeners = []),
                (this._platformStrategy = t);
              const r = this._platformStrategy.getBaseHref();
              (this._platformLocation = i),
                (this._baseHref = Vb(jb(r))),
                this._platformStrategy.onPopState((s) => {
                  this._subject.emit({
                    url: this.path(!0),
                    pop: !0,
                    state: s.state,
                    type: s.type,
                  });
                });
            }
            path(t = !1) {
              return this.normalize(this._platformStrategy.path(t));
            }
            getState() {
              return this._platformLocation.getState();
            }
            isCurrentPathEqualTo(t, i = "") {
              return this.path() == this.normalize(t + Xn(i));
            }
            normalize(t) {
              return n.stripTrailingSlash(
                (function oR(n, e) {
                  return n && e.startsWith(n) ? e.substring(n.length) : e;
                })(this._baseHref, jb(t))
              );
            }
            prepareExternalUrl(t) {
              return (
                t && "/" !== t[0] && (t = "/" + t),
                this._platformStrategy.prepareExternalUrl(t)
              );
            }
            go(t, i = "", r = null) {
              this._platformStrategy.pushState(r, "", t, i),
                this._notifyUrlChangeListeners(
                  this.prepareExternalUrl(t + Xn(i)),
                  r
                );
            }
            replaceState(t, i = "", r = null) {
              this._platformStrategy.replaceState(r, "", t, i),
                this._notifyUrlChangeListeners(
                  this.prepareExternalUrl(t + Xn(i)),
                  r
                );
            }
            forward() {
              this._platformStrategy.forward();
            }
            back() {
              this._platformStrategy.back();
            }
            historyGo(t = 0) {
              var i, r;
              null === (r = (i = this._platformStrategy).historyGo) ||
                void 0 === r ||
                r.call(i, t);
            }
            onUrlChange(t) {
              this._urlChangeListeners.push(t),
                this._urlChangeSubscription ||
                  (this._urlChangeSubscription = this.subscribe((i) => {
                    this._notifyUrlChangeListeners(i.url, i.state);
                  }));
            }
            _notifyUrlChangeListeners(t = "", i) {
              this._urlChangeListeners.forEach((r) => r(t, i));
            }
            subscribe(t, i, r) {
              return this._subject.subscribe({
                next: t,
                error: i,
                complete: r,
              });
            }
          }
          return (
            (n.normalizeQueryParams = Xn),
            (n.joinWithSlash = ch),
            (n.stripTrailingSlash = Vb),
            (n.ɵfac = function (t) {
              return new (t || n)(b(ns), b(qi));
            }),
            (n.ɵprov = I({
              token: n,
              factory: function () {
                return (function sR() {
                  return new ll(b(ns), b(qi));
                })();
              },
              providedIn: "root",
            })),
            n
          );
        })();
      function jb(n) {
        return n.replace(/\/index.html$/, "");
      }
      var ze = (() => (
        ((ze = ze || {})[(ze.Zero = 0)] = "Zero"),
        (ze[(ze.One = 1)] = "One"),
        (ze[(ze.Two = 2)] = "Two"),
        (ze[(ze.Few = 3)] = "Few"),
        (ze[(ze.Many = 4)] = "Many"),
        (ze[(ze.Other = 5)] = "Other"),
        ze
      ))();
      const fR = function Jy(n) {
        return (function _t(n) {
          const e = (function ZI(n) {
            return n.toLowerCase().replace(/_/g, "-");
          })(n);
          let t = ev(e);
          if (t) return t;
          const i = e.split("-")[0];
          if (((t = ev(i)), t)) return t;
          if ("en" === i) return YI;
          throw new Error(`Missing locale data for the locale "${n}".`);
        })(n)[S.PluralCase];
      };
      class yl {}
      let UR = (() => {
        class n extends yl {
          constructor(t) {
            super(), (this.locale = t);
          }
          getPluralCategory(t, i) {
            switch (fR(i || this.locale)(t)) {
              case ze.Zero:
                return "zero";
              case ze.One:
                return "one";
              case ze.Two:
                return "two";
              case ze.Few:
                return "few";
              case ze.Many:
                return "many";
              default:
                return "other";
            }
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(Qn));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      function Yb(n, e) {
        e = encodeURIComponent(e);
        for (const t of n.split(";")) {
          const i = t.indexOf("="),
            [r, s] = -1 == i ? [t, ""] : [t.slice(0, i), t.slice(i + 1)];
          if (r.trim() === e) return decodeURIComponent(s);
        }
        return null;
      }
      let Zb = (() => {
          class n {
            constructor(t, i, r, s) {
              (this._iterableDiffers = t),
                (this._keyValueDiffers = i),
                (this._ngEl = r),
                (this._renderer = s),
                (this._iterableDiffer = null),
                (this._keyValueDiffer = null),
                (this._initialClasses = []),
                (this._rawClass = null);
            }
            set klass(t) {
              this._removeClasses(this._initialClasses),
                (this._initialClasses =
                  "string" == typeof t ? t.split(/\s+/) : []),
                this._applyClasses(this._initialClasses),
                this._applyClasses(this._rawClass);
            }
            set ngClass(t) {
              this._removeClasses(this._rawClass),
                this._applyClasses(this._initialClasses),
                (this._iterableDiffer = null),
                (this._keyValueDiffer = null),
                (this._rawClass = "string" == typeof t ? t.split(/\s+/) : t),
                this._rawClass &&
                  (Qs(this._rawClass)
                    ? (this._iterableDiffer = this._iterableDiffers
                        .find(this._rawClass)
                        .create())
                    : (this._keyValueDiffer = this._keyValueDiffers
                        .find(this._rawClass)
                        .create()));
            }
            ngDoCheck() {
              if (this._iterableDiffer) {
                const t = this._iterableDiffer.diff(this._rawClass);
                t && this._applyIterableChanges(t);
              } else if (this._keyValueDiffer) {
                const t = this._keyValueDiffer.diff(this._rawClass);
                t && this._applyKeyValueChanges(t);
              }
            }
            _applyKeyValueChanges(t) {
              t.forEachAddedItem((i) =>
                this._toggleClass(i.key, i.currentValue)
              ),
                t.forEachChangedItem((i) =>
                  this._toggleClass(i.key, i.currentValue)
                ),
                t.forEachRemovedItem((i) => {
                  i.previousValue && this._toggleClass(i.key, !1);
                });
            }
            _applyIterableChanges(t) {
              t.forEachAddedItem((i) => {
                if ("string" != typeof i.item)
                  throw new Error(
                    `NgClass can only toggle CSS classes expressed as strings, got ${de(
                      i.item
                    )}`
                  );
                this._toggleClass(i.item, !0);
              }),
                t.forEachRemovedItem((i) => this._toggleClass(i.item, !1));
            }
            _applyClasses(t) {
              t &&
                (Array.isArray(t) || t instanceof Set
                  ? t.forEach((i) => this._toggleClass(i, !0))
                  : Object.keys(t).forEach((i) =>
                      this._toggleClass(i, !!t[i])
                    ));
            }
            _removeClasses(t) {
              t &&
                (Array.isArray(t) || t instanceof Set
                  ? t.forEach((i) => this._toggleClass(i, !1))
                  : Object.keys(t).forEach((i) => this._toggleClass(i, !1)));
            }
            _toggleClass(t, i) {
              (t = t.trim()) &&
                t.split(/\s+/g).forEach((r) => {
                  i
                    ? this._renderer.addClass(this._ngEl.nativeElement, r)
                    : this._renderer.removeClass(this._ngEl.nativeElement, r);
                });
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(mo), _(ts), _(Se), _(Yn));
            }),
            (n.ɵdir = x({
              type: n,
              selectors: [["", "ngClass", ""]],
              inputs: { klass: ["class", "klass"], ngClass: "ngClass" },
            })),
            n
          );
        })(),
        vl = (() => {
          class n {
            constructor(t, i) {
              (this._viewContainer = t),
                (this._context = new qR()),
                (this._thenTemplateRef = null),
                (this._elseTemplateRef = null),
                (this._thenViewRef = null),
                (this._elseViewRef = null),
                (this._thenTemplateRef = i);
            }
            set ngIf(t) {
              (this._context.$implicit = this._context.ngIf = t),
                this._updateView();
            }
            set ngIfThen(t) {
              Xb("ngIfThen", t),
                (this._thenTemplateRef = t),
                (this._thenViewRef = null),
                this._updateView();
            }
            set ngIfElse(t) {
              Xb("ngIfElse", t),
                (this._elseTemplateRef = t),
                (this._elseViewRef = null),
                this._updateView();
            }
            _updateView() {
              this._context.$implicit
                ? this._thenViewRef ||
                  (this._viewContainer.clear(),
                  (this._elseViewRef = null),
                  this._thenTemplateRef &&
                    (this._thenViewRef = this._viewContainer.createEmbeddedView(
                      this._thenTemplateRef,
                      this._context
                    )))
                : this._elseViewRef ||
                  (this._viewContainer.clear(),
                  (this._thenViewRef = null),
                  this._elseTemplateRef &&
                    (this._elseViewRef = this._viewContainer.createEmbeddedView(
                      this._elseTemplateRef,
                      this._context
                    )));
            }
            static ngTemplateContextGuard(t, i) {
              return !0;
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(Zt), _(Rn));
            }),
            (n.ɵdir = x({
              type: n,
              selectors: [["", "ngIf", ""]],
              inputs: {
                ngIf: "ngIf",
                ngIfThen: "ngIfThen",
                ngIfElse: "ngIfElse",
              },
            })),
            n
          );
        })();
      class qR {
        constructor() {
          (this.$implicit = null), (this.ngIf = null);
        }
      }
      function Xb(n, e) {
        if (e && !e.createEmbeddedView)
          throw new Error(
            `${n} must be a TemplateRef, but received '${de(e)}'.`
          );
      }
      class vh {
        constructor(e, t) {
          (this._viewContainerRef = e),
            (this._templateRef = t),
            (this._created = !1);
        }
        create() {
          (this._created = !0),
            this._viewContainerRef.createEmbeddedView(this._templateRef);
        }
        destroy() {
          (this._created = !1), this._viewContainerRef.clear();
        }
        enforceState(e) {
          e && !this._created
            ? this.create()
            : !e && this._created && this.destroy();
        }
      }
      let vo = (() => {
          class n {
            constructor() {
              (this._defaultUsed = !1),
                (this._caseCount = 0),
                (this._lastCaseCheckIndex = 0),
                (this._lastCasesMatched = !1);
            }
            set ngSwitch(t) {
              (this._ngSwitch = t),
                0 === this._caseCount && this._updateDefaultCases(!0);
            }
            _addCase() {
              return this._caseCount++;
            }
            _addDefault(t) {
              this._defaultViews || (this._defaultViews = []),
                this._defaultViews.push(t);
            }
            _matchCase(t) {
              const i = t == this._ngSwitch;
              return (
                (this._lastCasesMatched = this._lastCasesMatched || i),
                this._lastCaseCheckIndex++,
                this._lastCaseCheckIndex === this._caseCount &&
                  (this._updateDefaultCases(!this._lastCasesMatched),
                  (this._lastCaseCheckIndex = 0),
                  (this._lastCasesMatched = !1)),
                i
              );
            }
            _updateDefaultCases(t) {
              if (this._defaultViews && t !== this._defaultUsed) {
                this._defaultUsed = t;
                for (let i = 0; i < this._defaultViews.length; i++)
                  this._defaultViews[i].enforceState(t);
              }
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵdir = x({
              type: n,
              selectors: [["", "ngSwitch", ""]],
              inputs: { ngSwitch: "ngSwitch" },
            })),
            n
          );
        })(),
        bh = (() => {
          class n {
            constructor(t, i, r) {
              (this.ngSwitch = r), r._addCase(), (this._view = new vh(t, i));
            }
            ngDoCheck() {
              this._view.enforceState(
                this.ngSwitch._matchCase(this.ngSwitchCase)
              );
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(Zt), _(Rn), _(vo, 9));
            }),
            (n.ɵdir = x({
              type: n,
              selectors: [["", "ngSwitchCase", ""]],
              inputs: { ngSwitchCase: "ngSwitchCase" },
            })),
            n
          );
        })(),
        Jb = (() => {
          class n {
            constructor(t, i, r) {
              r._addDefault(new vh(t, i));
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(Zt), _(Rn), _(vo, 9));
            }),
            (n.ɵdir = x({ type: n, selectors: [["", "ngSwitchDefault", ""]] })),
            n
          );
        })(),
        bl = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({ providers: [{ provide: yl, useClass: UR }] })),
            n
          );
        })();
      const nC = "browser";
      let CP = (() => {
        class n {}
        return (
          (n.ɵprov = I({
            token: n,
            providedIn: "root",
            factory: () => new wP(b(ue), window),
          })),
          n
        );
      })();
      class wP {
        constructor(e, t) {
          (this.document = e), (this.window = t), (this.offset = () => [0, 0]);
        }
        setOffset(e) {
          this.offset = Array.isArray(e) ? () => e : e;
        }
        getScrollPosition() {
          return this.supportsScrolling()
            ? [this.window.pageXOffset, this.window.pageYOffset]
            : [0, 0];
        }
        scrollToPosition(e) {
          this.supportsScrolling() && this.window.scrollTo(e[0], e[1]);
        }
        scrollToAnchor(e) {
          if (!this.supportsScrolling()) return;
          const t = (function DP(n, e) {
            const t = n.getElementById(e) || n.getElementsByName(e)[0];
            if (t) return t;
            if (
              "function" == typeof n.createTreeWalker &&
              n.body &&
              (n.body.createShadowRoot || n.body.attachShadow)
            ) {
              const i = n.createTreeWalker(n.body, NodeFilter.SHOW_ELEMENT);
              let r = i.currentNode;
              for (; r; ) {
                const s = r.shadowRoot;
                if (s) {
                  const o =
                    s.getElementById(e) || s.querySelector(`[name="${e}"]`);
                  if (o) return o;
                }
                r = i.nextNode();
              }
            }
            return null;
          })(this.document, e);
          t && (this.scrollToElement(t), this.attemptFocus(t));
        }
        setHistoryScrollRestoration(e) {
          if (this.supportScrollRestoration()) {
            const t = this.window.history;
            t && t.scrollRestoration && (t.scrollRestoration = e);
          }
        }
        scrollToElement(e) {
          const t = e.getBoundingClientRect(),
            i = t.left + this.window.pageXOffset,
            r = t.top + this.window.pageYOffset,
            s = this.offset();
          this.window.scrollTo(i - s[0], r - s[1]);
        }
        attemptFocus(e) {
          return e.focus(), this.document.activeElement === e;
        }
        supportScrollRestoration() {
          try {
            if (!this.supportsScrolling()) return !1;
            const e =
              iC(this.window.history) ||
              iC(Object.getPrototypeOf(this.window.history));
            return !(!e || (!e.writable && !e.set));
          } catch (e) {
            return !1;
          }
        }
        supportsScrolling() {
          try {
            return (
              !!this.window &&
              !!this.window.scrollTo &&
              "pageXOffset" in this.window
            );
          } catch (e) {
            return !1;
          }
        }
      }
      function iC(n) {
        return Object.getOwnPropertyDescriptor(n, "scrollRestoration");
      }
      class rC {}
      class Dh extends class EP extends class JF {} {
        constructor() {
          super(...arguments), (this.supportsDOMEvents = !0);
        }
      } {
        static makeCurrent() {
          !(function XF(n) {
            al || (al = n);
          })(new Dh());
        }
        onAndCancel(e, t, i) {
          return (
            e.addEventListener(t, i, !1),
            () => {
              e.removeEventListener(t, i, !1);
            }
          );
        }
        dispatchEvent(e, t) {
          e.dispatchEvent(t);
        }
        remove(e) {
          e.parentNode && e.parentNode.removeChild(e);
        }
        createElement(e, t) {
          return (t = t || this.getDefaultDocument()).createElement(e);
        }
        createHtmlDocument() {
          return document.implementation.createHTMLDocument("fakeTitle");
        }
        getDefaultDocument() {
          return document;
        }
        isElementNode(e) {
          return e.nodeType === Node.ELEMENT_NODE;
        }
        isShadowRoot(e) {
          return e instanceof DocumentFragment;
        }
        getGlobalEventTarget(e, t) {
          return "window" === t
            ? window
            : "document" === t
            ? e
            : "body" === t
            ? e.body
            : null;
        }
        getBaseHref(e) {
          const t = (function MP() {
            return (
              (bo = bo || document.querySelector("base")),
              bo ? bo.getAttribute("href") : null
            );
          })();
          return null == t
            ? null
            : (function SP(n) {
                (Cl = Cl || document.createElement("a")),
                  Cl.setAttribute("href", n);
                const e = Cl.pathname;
                return "/" === e.charAt(0) ? e : `/${e}`;
              })(t);
        }
        resetBaseElement() {
          bo = null;
        }
        getUserAgent() {
          return window.navigator.userAgent;
        }
        getCookie(e) {
          return Yb(document.cookie, e);
        }
      }
      let Cl,
        bo = null;
      const sC = new T("TRANSITION_ID"),
        TP = [
          {
            provide: rl,
            useFactory: function AP(n, e, t) {
              return () => {
                t.get(Jr).donePromise.then(() => {
                  const i = Pn(),
                    r = e.querySelectorAll(`style[ng-transition="${n}"]`);
                  for (let s = 0; s < r.length; s++) i.remove(r[s]);
                });
              };
            },
            deps: [sC, ue, Qe],
            multi: !0,
          },
        ];
      class Eh {
        static init() {
          !(function yF(n) {
            ih = n;
          })(new Eh());
        }
        addToWindow(e) {
          (pe.getAngularTestability = (i, r = !0) => {
            const s = e.findTestabilityInTree(i, r);
            if (null == s)
              throw new Error("Could not find testability for element.");
            return s;
          }),
            (pe.getAllAngularTestabilities = () => e.getAllTestabilities()),
            (pe.getAllAngularRootElements = () => e.getAllRootElements()),
            pe.frameworkStabilizers || (pe.frameworkStabilizers = []),
            pe.frameworkStabilizers.push((i) => {
              const r = pe.getAllAngularTestabilities();
              let s = r.length,
                o = !1;
              const a = function (l) {
                (o = o || l), s--, 0 == s && i(o);
              };
              r.forEach(function (l) {
                l.whenStable(a);
              });
            });
        }
        findTestabilityInTree(e, t, i) {
          if (null == t) return null;
          const r = e.getTestability(t);
          return null != r
            ? r
            : i
            ? Pn().isShadowRoot(t)
              ? this.findTestabilityInTree(e, t.host, !0)
              : this.findTestabilityInTree(e, t.parentElement, !0)
            : null;
        }
      }
      let OP = (() => {
        class n {
          build() {
            return new XMLHttpRequest();
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      const wl = new T("EventManagerPlugins");
      let Dl = (() => {
        class n {
          constructor(t, i) {
            (this._zone = i),
              (this._eventNameToPlugin = new Map()),
              t.forEach((r) => (r.manager = this)),
              (this._plugins = t.slice().reverse());
          }
          addEventListener(t, i, r) {
            return this._findPluginFor(i).addEventListener(t, i, r);
          }
          addGlobalEventListener(t, i, r) {
            return this._findPluginFor(i).addGlobalEventListener(t, i, r);
          }
          getZone() {
            return this._zone;
          }
          _findPluginFor(t) {
            const i = this._eventNameToPlugin.get(t);
            if (i) return i;
            const r = this._plugins;
            for (let s = 0; s < r.length; s++) {
              const o = r[s];
              if (o.supports(t)) return this._eventNameToPlugin.set(t, o), o;
            }
            throw new Error(`No event manager plugin found for event ${t}`);
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(wl), b(ee));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      class oC {
        constructor(e) {
          this._doc = e;
        }
        addGlobalEventListener(e, t, i) {
          const r = Pn().getGlobalEventTarget(this._doc, e);
          if (!r)
            throw new Error(`Unsupported event target ${r} for event ${t}`);
          return this.addEventListener(r, t, i);
        }
      }
      let aC = (() => {
          class n {
            constructor() {
              this._stylesSet = new Set();
            }
            addStyles(t) {
              const i = new Set();
              t.forEach((r) => {
                this._stylesSet.has(r) || (this._stylesSet.add(r), i.add(r));
              }),
                this.onStylesAdded(i);
            }
            onStylesAdded(t) {}
            getAllStyles() {
              return Array.from(this._stylesSet);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })(),
        Co = (() => {
          class n extends aC {
            constructor(t) {
              super(),
                (this._doc = t),
                (this._hostNodes = new Map()),
                this._hostNodes.set(t.head, []);
            }
            _addStylesToHost(t, i, r) {
              t.forEach((s) => {
                const o = this._doc.createElement("style");
                (o.textContent = s), r.push(i.appendChild(o));
              });
            }
            addHost(t) {
              const i = [];
              this._addStylesToHost(this._stylesSet, t, i),
                this._hostNodes.set(t, i);
            }
            removeHost(t) {
              const i = this._hostNodes.get(t);
              i && i.forEach(lC), this._hostNodes.delete(t);
            }
            onStylesAdded(t) {
              this._hostNodes.forEach((i, r) => {
                this._addStylesToHost(t, r, i);
              });
            }
            ngOnDestroy() {
              this._hostNodes.forEach((t) => t.forEach(lC));
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(ue));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })();
      function lC(n) {
        Pn().remove(n);
      }
      const Mh = {
          svg: "http://www.w3.org/2000/svg",
          xhtml: "http://www.w3.org/1999/xhtml",
          xlink: "http://www.w3.org/1999/xlink",
          xml: "http://www.w3.org/XML/1998/namespace",
          xmlns: "http://www.w3.org/2000/xmlns/",
        },
        Sh = /%COMP%/g;
      function El(n, e, t) {
        for (let i = 0; i < e.length; i++) {
          let r = e[i];
          Array.isArray(r) ? El(n, r, t) : ((r = r.replace(Sh, n)), t.push(r));
        }
        return t;
      }
      function dC(n) {
        return (e) => {
          if ("__ngUnwrap__" === e) return n;
          !1 === n(e) && (e.preventDefault(), (e.returnValue = !1));
        };
      }
      let Ml = (() => {
        class n {
          constructor(t, i, r) {
            (this.eventManager = t),
              (this.sharedStylesHost = i),
              (this.appId = r),
              (this.rendererByCompId = new Map()),
              (this.defaultRenderer = new Ah(t));
          }
          createRenderer(t, i) {
            if (!t || !i) return this.defaultRenderer;
            switch (i.encapsulation) {
              case an.Emulated: {
                let r = this.rendererByCompId.get(i.id);
                return (
                  r ||
                    ((r = new PP(
                      this.eventManager,
                      this.sharedStylesHost,
                      i,
                      this.appId
                    )),
                    this.rendererByCompId.set(i.id, r)),
                  r.applyToHost(t),
                  r
                );
              }
              case 1:
              case an.ShadowDom:
                return new NP(this.eventManager, this.sharedStylesHost, t, i);
              default:
                if (!this.rendererByCompId.has(i.id)) {
                  const r = El(i.id, i.styles, []);
                  this.sharedStylesHost.addStyles(r),
                    this.rendererByCompId.set(i.id, this.defaultRenderer);
                }
                return this.defaultRenderer;
            }
          }
          begin() {}
          end() {}
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(Dl), b(Co), b(po));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      class Ah {
        constructor(e) {
          (this.eventManager = e),
            (this.data = Object.create(null)),
            (this.destroyNode = null);
        }
        destroy() {}
        createElement(e, t) {
          return t
            ? document.createElementNS(Mh[t] || t, e)
            : document.createElement(e);
        }
        createComment(e) {
          return document.createComment(e);
        }
        createText(e) {
          return document.createTextNode(e);
        }
        appendChild(e, t) {
          e.appendChild(t);
        }
        insertBefore(e, t, i) {
          e && e.insertBefore(t, i);
        }
        removeChild(e, t) {
          e && e.removeChild(t);
        }
        selectRootElement(e, t) {
          let i = "string" == typeof e ? document.querySelector(e) : e;
          if (!i)
            throw new Error(`The selector "${e}" did not match any elements`);
          return t || (i.textContent = ""), i;
        }
        parentNode(e) {
          return e.parentNode;
        }
        nextSibling(e) {
          return e.nextSibling;
        }
        setAttribute(e, t, i, r) {
          if (r) {
            t = r + ":" + t;
            const s = Mh[r];
            s ? e.setAttributeNS(s, t, i) : e.setAttribute(t, i);
          } else e.setAttribute(t, i);
        }
        removeAttribute(e, t, i) {
          if (i) {
            const r = Mh[i];
            r ? e.removeAttributeNS(r, t) : e.removeAttribute(`${i}:${t}`);
          } else e.removeAttribute(t);
        }
        addClass(e, t) {
          e.classList.add(t);
        }
        removeClass(e, t) {
          e.classList.remove(t);
        }
        setStyle(e, t, i, r) {
          r & (kt.DashCase | kt.Important)
            ? e.style.setProperty(t, i, r & kt.Important ? "important" : "")
            : (e.style[t] = i);
        }
        removeStyle(e, t, i) {
          i & kt.DashCase ? e.style.removeProperty(t) : (e.style[t] = "");
        }
        setProperty(e, t, i) {
          e[t] = i;
        }
        setValue(e, t) {
          e.nodeValue = t;
        }
        listen(e, t, i) {
          return "string" == typeof e
            ? this.eventManager.addGlobalEventListener(e, t, dC(i))
            : this.eventManager.addEventListener(e, t, dC(i));
        }
      }
      class PP extends Ah {
        constructor(e, t, i, r) {
          super(e), (this.component = i);
          const s = El(r + "-" + i.id, i.styles, []);
          t.addStyles(s),
            (this.contentAttr = (function kP(n) {
              return "_ngcontent-%COMP%".replace(Sh, n);
            })(r + "-" + i.id)),
            (this.hostAttr = (function FP(n) {
              return "_nghost-%COMP%".replace(Sh, n);
            })(r + "-" + i.id));
        }
        applyToHost(e) {
          super.setAttribute(e, this.hostAttr, "");
        }
        createElement(e, t) {
          const i = super.createElement(e, t);
          return super.setAttribute(i, this.contentAttr, ""), i;
        }
      }
      class NP extends Ah {
        constructor(e, t, i, r) {
          super(e),
            (this.sharedStylesHost = t),
            (this.hostEl = i),
            (this.shadowRoot = i.attachShadow({ mode: "open" })),
            this.sharedStylesHost.addHost(this.shadowRoot);
          const s = El(r.id, r.styles, []);
          for (let o = 0; o < s.length; o++) {
            const a = document.createElement("style");
            (a.textContent = s[o]), this.shadowRoot.appendChild(a);
          }
        }
        nodeOrShadowRoot(e) {
          return e === this.hostEl ? this.shadowRoot : e;
        }
        destroy() {
          this.sharedStylesHost.removeHost(this.shadowRoot);
        }
        appendChild(e, t) {
          return super.appendChild(this.nodeOrShadowRoot(e), t);
        }
        insertBefore(e, t, i) {
          return super.insertBefore(this.nodeOrShadowRoot(e), t, i);
        }
        removeChild(e, t) {
          return super.removeChild(this.nodeOrShadowRoot(e), t);
        }
        parentNode(e) {
          return this.nodeOrShadowRoot(
            super.parentNode(this.nodeOrShadowRoot(e))
          );
        }
      }
      let LP = (() => {
        class n extends oC {
          constructor(t) {
            super(t);
          }
          supports(t) {
            return !0;
          }
          addEventListener(t, i, r) {
            return (
              t.addEventListener(i, r, !1),
              () => this.removeEventListener(t, i, r)
            );
          }
          removeEventListener(t, i, r) {
            return t.removeEventListener(i, r);
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(ue));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      const fC = ["alt", "control", "meta", "shift"],
        BP = {
          "\b": "Backspace",
          "\t": "Tab",
          "\x7f": "Delete",
          "\x1b": "Escape",
          Del: "Delete",
          Esc: "Escape",
          Left: "ArrowLeft",
          Right: "ArrowRight",
          Up: "ArrowUp",
          Down: "ArrowDown",
          Menu: "ContextMenu",
          Scroll: "ScrollLock",
          Win: "OS",
        },
        pC = {
          A: "1",
          B: "2",
          C: "3",
          D: "4",
          E: "5",
          F: "6",
          G: "7",
          H: "8",
          I: "9",
          J: "*",
          K: "+",
          M: "-",
          N: ".",
          O: "/",
          "`": "0",
          "\x90": "NumLock",
        },
        jP = {
          alt: (n) => n.altKey,
          control: (n) => n.ctrlKey,
          meta: (n) => n.metaKey,
          shift: (n) => n.shiftKey,
        };
      let HP = (() => {
        class n extends oC {
          constructor(t) {
            super(t);
          }
          supports(t) {
            return null != n.parseEventName(t);
          }
          addEventListener(t, i, r) {
            const s = n.parseEventName(i),
              o = n.eventCallback(s.fullKey, r, this.manager.getZone());
            return this.manager
              .getZone()
              .runOutsideAngular(() => Pn().onAndCancel(t, s.domEventName, o));
          }
          static parseEventName(t) {
            const i = t.toLowerCase().split("."),
              r = i.shift();
            if (0 === i.length || ("keydown" !== r && "keyup" !== r))
              return null;
            const s = n._normalizeKey(i.pop());
            let o = "";
            if (
              (fC.forEach((l) => {
                const c = i.indexOf(l);
                c > -1 && (i.splice(c, 1), (o += l + "."));
              }),
              (o += s),
              0 != i.length || 0 === s.length)
            )
              return null;
            const a = {};
            return (a.domEventName = r), (a.fullKey = o), a;
          }
          static getEventFullKey(t) {
            let i = "",
              r = (function UP(n) {
                let e = n.key;
                if (null == e) {
                  if (((e = n.keyIdentifier), null == e)) return "Unidentified";
                  e.startsWith("U+") &&
                    ((e = String.fromCharCode(parseInt(e.substring(2), 16))),
                    3 === n.location && pC.hasOwnProperty(e) && (e = pC[e]));
                }
                return BP[e] || e;
              })(t);
            return (
              (r = r.toLowerCase()),
              " " === r ? (r = "space") : "." === r && (r = "dot"),
              fC.forEach((s) => {
                s != r && jP[s](t) && (i += s + ".");
              }),
              (i += r),
              i
            );
          }
          static eventCallback(t, i, r) {
            return (s) => {
              n.getEventFullKey(s) === t && r.runGuarded(() => i(s));
            };
          }
          static _normalizeKey(t) {
            return "esc" === t ? "escape" : t;
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(ue));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      const qP = yb($F, "browser", [
          { provide: go, useValue: nC },
          {
            provide: cb,
            useValue: function $P() {
              Dh.makeCurrent(), Eh.init();
            },
            multi: !0,
          },
          {
            provide: ue,
            useFactory: function GP() {
              return (
                (function J0(n) {
                  Jc = n;
                })(document),
                document
              );
            },
            deps: [],
          },
        ]),
        WP = [
          { provide: fd, useValue: "root" },
          {
            provide: Tr,
            useFactory: function zP() {
              return new Tr();
            },
            deps: [],
          },
          { provide: wl, useClass: LP, multi: !0, deps: [ue, ee, go] },
          { provide: wl, useClass: HP, multi: !0, deps: [ue] },
          { provide: Ml, useClass: Ml, deps: [Dl, Co, po] },
          { provide: ao, useExisting: Ml },
          { provide: aC, useExisting: Co },
          { provide: Co, useClass: Co, deps: [ue] },
          { provide: nh, useClass: nh, deps: [ee] },
          { provide: Dl, useClass: Dl, deps: [wl, ee] },
          { provide: rC, useClass: OP, deps: [] },
        ];
      let gC = (() => {
        class n {
          constructor(t) {
            if (t)
              throw new Error(
                "BrowserModule has already been loaded. If you need access to common directives such as NgIf and NgFor from a lazy loaded module, import CommonModule instead."
              );
          }
          static withServerTransition(t) {
            return {
              ngModule: n,
              providers: [
                { provide: po, useValue: t.appId },
                { provide: sC, useExisting: po },
                TP,
              ],
            };
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(n, 12));
          }),
          (n.ɵmod = he({ type: n })),
          (n.ɵinj = ce({ providers: WP, imports: [bl, ZF] })),
          n
        );
      })();
      function je(n) {
        return null != n && "false" != `${n}`;
      }
      function Oh(n, e = 0) {
        return (function s1(n) {
          return !isNaN(parseFloat(n)) && !isNaN(Number(n));
        })(n)
          ? Number(n)
          : e;
      }
      function yC(n) {
        return Array.isArray(n) ? n : [n];
      }
      function qe(n) {
        return null == n ? "" : "string" == typeof n ? n : `${n}px`;
      }
      function ei(n) {
        return n instanceof Se ? n.nativeElement : n;
      }
      "undefined" != typeof window && window;
      class vC {
        constructor(e = !1, t, i = !0) {
          (this._multiple = e),
            (this._emitChanges = i),
            (this._selection = new Set()),
            (this._deselectedToEmit = []),
            (this._selectedToEmit = []),
            (this.changed = new le()),
            t &&
              t.length &&
              (e
                ? t.forEach((r) => this._markSelected(r))
                : this._markSelected(t[0]),
              (this._selectedToEmit.length = 0));
        }
        get selected() {
          return (
            this._selected ||
              (this._selected = Array.from(this._selection.values())),
            this._selected
          );
        }
        select(...e) {
          this._verifyValueAssignment(e),
            e.forEach((t) => this._markSelected(t)),
            this._emitChangeEvent();
        }
        deselect(...e) {
          this._verifyValueAssignment(e),
            e.forEach((t) => this._unmarkSelected(t)),
            this._emitChangeEvent();
        }
        toggle(e) {
          this.isSelected(e) ? this.deselect(e) : this.select(e);
        }
        clear() {
          this._unmarkAll(), this._emitChangeEvent();
        }
        isSelected(e) {
          return this._selection.has(e);
        }
        isEmpty() {
          return 0 === this._selection.size;
        }
        hasValue() {
          return !this.isEmpty();
        }
        sort(e) {
          this._multiple && this.selected && this._selected.sort(e);
        }
        isMultipleSelection() {
          return this._multiple;
        }
        _emitChangeEvent() {
          (this._selected = null),
            (this._selectedToEmit.length || this._deselectedToEmit.length) &&
              (this.changed.next({
                source: this,
                added: this._selectedToEmit,
                removed: this._deselectedToEmit,
              }),
              (this._deselectedToEmit = []),
              (this._selectedToEmit = []));
        }
        _markSelected(e) {
          this.isSelected(e) ||
            (this._multiple || this._unmarkAll(),
            this._selection.add(e),
            this._emitChanges && this._selectedToEmit.push(e));
        }
        _unmarkSelected(e) {
          this.isSelected(e) &&
            (this._selection.delete(e),
            this._emitChanges && this._deselectedToEmit.push(e));
        }
        _unmarkAll() {
          this.isEmpty() ||
            this._selection.forEach((e) => this._unmarkSelected(e));
        }
        _verifyValueAssignment(e) {}
      }
      const { isArray: o1 } = Array,
        { getPrototypeOf: a1, prototype: l1, keys: c1 } = Object;
      function bC(n) {
        if (1 === n.length) {
          const e = n[0];
          if (o1(e)) return { args: e, keys: null };
          if (
            (function u1(n) {
              return n && "object" == typeof n && a1(n) === l1;
            })(e)
          ) {
            const t = c1(e);
            return { args: t.map((i) => e[i]), keys: t };
          }
        }
        return { args: n, keys: null };
      }
      const { isArray: d1 } = Array;
      function Ih(n) {
        return re((e) =>
          (function h1(n, e) {
            return d1(e) ? n(...e) : n(e);
          })(n, e)
        );
      }
      function CC(n, e) {
        return n.reduce((t, i, r) => ((t[i] = e[r]), t), {});
      }
      let wC = (() => {
          class n {
            constructor(t, i) {
              (this._renderer = t),
                (this._elementRef = i),
                (this.onChange = (r) => {}),
                (this.onTouched = () => {});
            }
            setProperty(t, i) {
              this._renderer.setProperty(this._elementRef.nativeElement, t, i);
            }
            registerOnTouched(t) {
              this.onTouched = t;
            }
            registerOnChange(t) {
              this.onChange = t;
            }
            setDisabledState(t) {
              this.setProperty("disabled", t);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(Yn), _(Se));
            }),
            (n.ɵdir = x({ type: n })),
            n
          );
        })(),
        Wi = (() => {
          class n extends wC {}
          return (
            (n.ɵfac = (function () {
              let e;
              return function (i) {
                return (e || (e = gt(n)))(i || n);
              };
            })()),
            (n.ɵdir = x({ type: n, features: [se] })),
            n
          );
        })();
      const vn = new T("NgValueAccessor"),
        g1 = { provide: vn, useExisting: _e(() => Sl), multi: !0 },
        _1 = new T("CompositionEventMode");
      let Sl = (() => {
        class n extends wC {
          constructor(t, i, r) {
            super(t, i),
              (this._compositionMode = r),
              (this._composing = !1),
              null == this._compositionMode &&
                (this._compositionMode = !(function m1() {
                  const n = Pn() ? Pn().getUserAgent() : "";
                  return /android (\d+)/.test(n.toLowerCase());
                })());
          }
          writeValue(t) {
            this.setProperty("value", null == t ? "" : t);
          }
          _handleInput(t) {
            (!this._compositionMode ||
              (this._compositionMode && !this._composing)) &&
              this.onChange(t);
          }
          _compositionStart() {
            this._composing = !0;
          }
          _compositionEnd(t) {
            (this._composing = !1), this._compositionMode && this.onChange(t);
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(_(Yn), _(Se), _(_1, 8));
          }),
          (n.ɵdir = x({
            type: n,
            selectors: [
              ["input", "formControlName", "", 3, "type", "checkbox"],
              ["textarea", "formControlName", ""],
              ["input", "formControl", "", 3, "type", "checkbox"],
              ["textarea", "formControl", ""],
              ["input", "ngModel", "", 3, "type", "checkbox"],
              ["textarea", "ngModel", ""],
              ["", "ngDefaultControl", ""],
            ],
            hostBindings: function (t, i) {
              1 & t &&
                Z("input", function (s) {
                  return i._handleInput(s.target.value);
                })("blur", function () {
                  return i.onTouched();
                })("compositionstart", function () {
                  return i._compositionStart();
                })("compositionend", function (s) {
                  return i._compositionEnd(s.target.value);
                });
            },
            features: [ge([g1]), se],
          })),
          n
        );
      })();
      function Ci(n) {
        return null == n || 0 === n.length;
      }
      function EC(n) {
        return null != n && "number" == typeof n.length;
      }
      const dt = new T("NgValidators"),
        wi = new T("NgAsyncValidators"),
        y1 =
          /^(?=.{1,254}$)(?=.{1,64}@)[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
      class Al {
        static min(e) {
          return (function MC(n) {
            return (e) => {
              if (Ci(e.value) || Ci(n)) return null;
              const t = parseFloat(e.value);
              return !isNaN(t) && t < n
                ? { min: { min: n, actual: e.value } }
                : null;
            };
          })(e);
        }
        static max(e) {
          return (function SC(n) {
            return (e) => {
              if (Ci(e.value) || Ci(n)) return null;
              const t = parseFloat(e.value);
              return !isNaN(t) && t > n
                ? { max: { max: n, actual: e.value } }
                : null;
            };
          })(e);
        }
        static required(e) {
          return (function AC(n) {
            return Ci(n.value) ? { required: !0 } : null;
          })(e);
        }
        static requiredTrue(e) {
          return (function TC(n) {
            return !0 === n.value ? null : { required: !0 };
          })(e);
        }
        static email(e) {
          return (function OC(n) {
            return Ci(n.value) || y1.test(n.value) ? null : { email: !0 };
          })(e);
        }
        static minLength(e) {
          return (function IC(n) {
            return (e) =>
              Ci(e.value) || !EC(e.value)
                ? null
                : e.value.length < n
                ? {
                    minlength: {
                      requiredLength: n,
                      actualLength: e.value.length,
                    },
                  }
                : null;
          })(e);
        }
        static maxLength(e) {
          return (function xC(n) {
            return (e) =>
              EC(e.value) && e.value.length > n
                ? {
                    maxlength: {
                      requiredLength: n,
                      actualLength: e.value.length,
                    },
                  }
                : null;
          })(e);
        }
        static pattern(e) {
          return (function kC(n) {
            if (!n) return wo;
            let e, t;
            return (
              "string" == typeof n
                ? ((t = ""),
                  "^" !== n.charAt(0) && (t += "^"),
                  (t += n),
                  "$" !== n.charAt(n.length - 1) && (t += "$"),
                  (e = new RegExp(t)))
                : ((t = n.toString()), (e = n)),
              (i) => {
                if (Ci(i.value)) return null;
                const r = i.value;
                return e.test(r)
                  ? null
                  : { pattern: { requiredPattern: t, actualValue: r } };
              }
            );
          })(e);
        }
        static nullValidator(e) {
          return null;
        }
        static compose(e) {
          return VC(e);
        }
        static composeAsync(e) {
          return BC(e);
        }
      }
      function wo(n) {
        return null;
      }
      function FC(n) {
        return null != n;
      }
      function RC(n) {
        const e = Js(n) ? et(n) : n;
        return Sd(e), e;
      }
      function PC(n) {
        let e = {};
        return (
          n.forEach((t) => {
            e = null != t ? Object.assign(Object.assign({}, e), t) : e;
          }),
          0 === Object.keys(e).length ? null : e
        );
      }
      function NC(n, e) {
        return e.map((t) => t(n));
      }
      function LC(n) {
        return n.map((e) =>
          (function v1(n) {
            return !n.validate;
          })(e)
            ? e
            : (t) => e.validate(t)
        );
      }
      function VC(n) {
        if (!n) return null;
        const e = n.filter(FC);
        return 0 == e.length
          ? null
          : function (t) {
              return PC(NC(t, e));
            };
      }
      function xh(n) {
        return null != n ? VC(LC(n)) : null;
      }
      function BC(n) {
        if (!n) return null;
        const e = n.filter(FC);
        return 0 == e.length
          ? null
          : function (t) {
              return (function f1(...n) {
                const e = Xp(n),
                  { args: t, keys: i } = bC(n),
                  r = new fe((s) => {
                    const { length: o } = t;
                    if (!o) return void s.complete();
                    const a = new Array(o);
                    let l = o,
                      c = o;
                    for (let u = 0; u < o; u++) {
                      let d = !1;
                      St(t[u]).subscribe(
                        new De(
                          s,
                          (h) => {
                            d || ((d = !0), c--), (a[u] = h);
                          },
                          () => l--,
                          void 0,
                          () => {
                            (!l || !d) &&
                              (c || s.next(i ? CC(i, a) : a), s.complete());
                          }
                        )
                      );
                    }
                  });
                return e ? r.pipe(Ih(e)) : r;
              })(NC(t, e).map(RC)).pipe(re(PC));
            };
      }
      function kh(n) {
        return null != n ? BC(LC(n)) : null;
      }
      function jC(n, e) {
        return null === n ? [e] : Array.isArray(n) ? [...n, e] : [n, e];
      }
      function HC(n) {
        return n._rawValidators;
      }
      function UC(n) {
        return n._rawAsyncValidators;
      }
      function Fh(n) {
        return n ? (Array.isArray(n) ? n : [n]) : [];
      }
      function Tl(n, e) {
        return Array.isArray(n) ? n.includes(e) : n === e;
      }
      function $C(n, e) {
        const t = Fh(e);
        return (
          Fh(n).forEach((r) => {
            Tl(t, r) || t.push(r);
          }),
          t
        );
      }
      function zC(n, e) {
        return Fh(e).filter((t) => !Tl(n, t));
      }
      class GC {
        constructor() {
          (this._rawValidators = []),
            (this._rawAsyncValidators = []),
            (this._onDestroyCallbacks = []);
        }
        get value() {
          return this.control ? this.control.value : null;
        }
        get valid() {
          return this.control ? this.control.valid : null;
        }
        get invalid() {
          return this.control ? this.control.invalid : null;
        }
        get pending() {
          return this.control ? this.control.pending : null;
        }
        get disabled() {
          return this.control ? this.control.disabled : null;
        }
        get enabled() {
          return this.control ? this.control.enabled : null;
        }
        get errors() {
          return this.control ? this.control.errors : null;
        }
        get pristine() {
          return this.control ? this.control.pristine : null;
        }
        get dirty() {
          return this.control ? this.control.dirty : null;
        }
        get touched() {
          return this.control ? this.control.touched : null;
        }
        get status() {
          return this.control ? this.control.status : null;
        }
        get untouched() {
          return this.control ? this.control.untouched : null;
        }
        get statusChanges() {
          return this.control ? this.control.statusChanges : null;
        }
        get valueChanges() {
          return this.control ? this.control.valueChanges : null;
        }
        get path() {
          return null;
        }
        _setValidators(e) {
          (this._rawValidators = e || []),
            (this._composedValidatorFn = xh(this._rawValidators));
        }
        _setAsyncValidators(e) {
          (this._rawAsyncValidators = e || []),
            (this._composedAsyncValidatorFn = kh(this._rawAsyncValidators));
        }
        get validator() {
          return this._composedValidatorFn || null;
        }
        get asyncValidator() {
          return this._composedAsyncValidatorFn || null;
        }
        _registerOnDestroy(e) {
          this._onDestroyCallbacks.push(e);
        }
        _invokeOnDestroyCallbacks() {
          this._onDestroyCallbacks.forEach((e) => e()),
            (this._onDestroyCallbacks = []);
        }
        reset(e) {
          this.control && this.control.reset(e);
        }
        hasError(e, t) {
          return !!this.control && this.control.hasError(e, t);
        }
        getError(e, t) {
          return this.control ? this.control.getError(e, t) : null;
        }
      }
      class Nn extends GC {
        constructor() {
          super(...arguments),
            (this._parent = null),
            (this.name = null),
            (this.valueAccessor = null);
        }
      }
      class vt extends GC {
        get formDirective() {
          return null;
        }
        get path() {
          return null;
        }
      }
      let WC = (() => {
        class n extends class qC {
          constructor(e) {
            this._cd = e;
          }
          is(e) {
            var t, i, r;
            return "submitted" === e
              ? !!(null === (t = this._cd) || void 0 === t
                  ? void 0
                  : t.submitted)
              : !!(null ===
                  (r =
                    null === (i = this._cd) || void 0 === i
                      ? void 0
                      : i.control) || void 0 === r
                  ? void 0
                  : r[e]);
          }
        } {
          constructor(t) {
            super(t);
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(_(Nn, 2));
          }),
          (n.ɵdir = x({
            type: n,
            selectors: [
              ["", "formControlName", ""],
              ["", "ngModel", ""],
              ["", "formControl", ""],
            ],
            hostVars: 14,
            hostBindings: function (t, i) {
              2 & t &&
                Dt("ng-untouched", i.is("untouched"))(
                  "ng-touched",
                  i.is("touched")
                )("ng-pristine", i.is("pristine"))("ng-dirty", i.is("dirty"))(
                  "ng-valid",
                  i.is("valid")
                )("ng-invalid", i.is("invalid"))("ng-pending", i.is("pending"));
            },
            features: [se],
          })),
          n
        );
      })();
      function Do(n, e) {
        Nh(n, e),
          e.valueAccessor.writeValue(n.value),
          (function T1(n, e) {
            e.valueAccessor.registerOnChange((t) => {
              (n._pendingValue = t),
                (n._pendingChange = !0),
                (n._pendingDirty = !0),
                "change" === n.updateOn && YC(n, e);
            });
          })(n, e),
          (function I1(n, e) {
            const t = (i, r) => {
              e.valueAccessor.writeValue(i), r && e.viewToModelUpdate(i);
            };
            n.registerOnChange(t),
              e._registerOnDestroy(() => {
                n._unregisterOnChange(t);
              });
          })(n, e),
          (function O1(n, e) {
            e.valueAccessor.registerOnTouched(() => {
              (n._pendingTouched = !0),
                "blur" === n.updateOn && n._pendingChange && YC(n, e),
                "submit" !== n.updateOn && n.markAsTouched();
            });
          })(n, e),
          (function A1(n, e) {
            if (e.valueAccessor.setDisabledState) {
              const t = (i) => {
                e.valueAccessor.setDisabledState(i);
              };
              n.registerOnDisabledChange(t),
                e._registerOnDestroy(() => {
                  n._unregisterOnDisabledChange(t);
                });
            }
          })(n, e);
      }
      function xl(n, e, t = !0) {
        const i = () => {};
        e.valueAccessor &&
          (e.valueAccessor.registerOnChange(i),
          e.valueAccessor.registerOnTouched(i)),
          Fl(n, e),
          n &&
            (e._invokeOnDestroyCallbacks(),
            n._registerOnCollectionChange(() => {}));
      }
      function kl(n, e) {
        n.forEach((t) => {
          t.registerOnValidatorChange && t.registerOnValidatorChange(e);
        });
      }
      function Nh(n, e) {
        const t = HC(n);
        null !== e.validator
          ? n.setValidators(jC(t, e.validator))
          : "function" == typeof t && n.setValidators([t]);
        const i = UC(n);
        null !== e.asyncValidator
          ? n.setAsyncValidators(jC(i, e.asyncValidator))
          : "function" == typeof i && n.setAsyncValidators([i]);
        const r = () => n.updateValueAndValidity();
        kl(e._rawValidators, r), kl(e._rawAsyncValidators, r);
      }
      function Fl(n, e) {
        let t = !1;
        if (null !== n) {
          if (null !== e.validator) {
            const r = HC(n);
            if (Array.isArray(r) && r.length > 0) {
              const s = r.filter((o) => o !== e.validator);
              s.length !== r.length && ((t = !0), n.setValidators(s));
            }
          }
          if (null !== e.asyncValidator) {
            const r = UC(n);
            if (Array.isArray(r) && r.length > 0) {
              const s = r.filter((o) => o !== e.asyncValidator);
              s.length !== r.length && ((t = !0), n.setAsyncValidators(s));
            }
          }
        }
        const i = () => {};
        return kl(e._rawValidators, i), kl(e._rawAsyncValidators, i), t;
      }
      function YC(n, e) {
        n._pendingDirty && n.markAsDirty(),
          n.setValue(n._pendingValue, { emitModelToViewChange: !1 }),
          e.viewToModelUpdate(n._pendingValue),
          (n._pendingChange = !1);
      }
      function ZC(n, e) {
        Nh(n, e);
      }
      function QC(n, e) {
        n._syncPendingControls(),
          e.forEach((t) => {
            const i = t.control;
            "submit" === i.updateOn &&
              i._pendingChange &&
              (t.viewToModelUpdate(i._pendingValue), (i._pendingChange = !1));
          });
      }
      function Rl(n, e) {
        const t = n.indexOf(e);
        t > -1 && n.splice(t, 1);
      }
      const Eo = "VALID",
        Pl = "INVALID",
        is = "PENDING",
        Mo = "DISABLED";
      function jh(n) {
        return (Uh(n) ? n.validators : n) || null;
      }
      function XC(n) {
        return Array.isArray(n) ? xh(n) : n || null;
      }
      function Hh(n, e) {
        return (Uh(e) ? e.asyncValidators : n) || null;
      }
      function JC(n) {
        return Array.isArray(n) ? kh(n) : n || null;
      }
      function Uh(n) {
        return null != n && !Array.isArray(n) && "object" == typeof n;
      }
      const ew = (n) => n instanceof rs,
        $h = (n) => n instanceof Gh;
      function tw(n) {
        return ew(n) ? n.value : n.getRawValue();
      }
      function nw(n, e) {
        const t = $h(n),
          i = n.controls;
        if (!(t ? Object.keys(i) : i).length) throw new ne(1e3, "");
        if (!i[e]) throw new ne(1001, "");
      }
      function iw(n, e) {
        $h(n),
          n._forEachChild((i, r) => {
            if (void 0 === e[r]) throw new ne(1002, "");
          });
      }
      class zh {
        constructor(e, t) {
          (this._pendingDirty = !1),
            (this._hasOwnPendingAsyncValidator = !1),
            (this._pendingTouched = !1),
            (this._onCollectionChange = () => {}),
            (this._parent = null),
            (this.pristine = !0),
            (this.touched = !1),
            (this._onDisabledChange = []),
            (this._rawValidators = e),
            (this._rawAsyncValidators = t),
            (this._composedValidatorFn = XC(this._rawValidators)),
            (this._composedAsyncValidatorFn = JC(this._rawAsyncValidators));
        }
        get validator() {
          return this._composedValidatorFn;
        }
        set validator(e) {
          this._rawValidators = this._composedValidatorFn = e;
        }
        get asyncValidator() {
          return this._composedAsyncValidatorFn;
        }
        set asyncValidator(e) {
          this._rawAsyncValidators = this._composedAsyncValidatorFn = e;
        }
        get parent() {
          return this._parent;
        }
        get valid() {
          return this.status === Eo;
        }
        get invalid() {
          return this.status === Pl;
        }
        get pending() {
          return this.status == is;
        }
        get disabled() {
          return this.status === Mo;
        }
        get enabled() {
          return this.status !== Mo;
        }
        get dirty() {
          return !this.pristine;
        }
        get untouched() {
          return !this.touched;
        }
        get updateOn() {
          return this._updateOn
            ? this._updateOn
            : this.parent
            ? this.parent.updateOn
            : "change";
        }
        setValidators(e) {
          (this._rawValidators = e), (this._composedValidatorFn = XC(e));
        }
        setAsyncValidators(e) {
          (this._rawAsyncValidators = e),
            (this._composedAsyncValidatorFn = JC(e));
        }
        addValidators(e) {
          this.setValidators($C(e, this._rawValidators));
        }
        addAsyncValidators(e) {
          this.setAsyncValidators($C(e, this._rawAsyncValidators));
        }
        removeValidators(e) {
          this.setValidators(zC(e, this._rawValidators));
        }
        removeAsyncValidators(e) {
          this.setAsyncValidators(zC(e, this._rawAsyncValidators));
        }
        hasValidator(e) {
          return Tl(this._rawValidators, e);
        }
        hasAsyncValidator(e) {
          return Tl(this._rawAsyncValidators, e);
        }
        clearValidators() {
          this.validator = null;
        }
        clearAsyncValidators() {
          this.asyncValidator = null;
        }
        markAsTouched(e = {}) {
          (this.touched = !0),
            this._parent && !e.onlySelf && this._parent.markAsTouched(e);
        }
        markAllAsTouched() {
          this.markAsTouched({ onlySelf: !0 }),
            this._forEachChild((e) => e.markAllAsTouched());
        }
        markAsUntouched(e = {}) {
          (this.touched = !1),
            (this._pendingTouched = !1),
            this._forEachChild((t) => {
              t.markAsUntouched({ onlySelf: !0 });
            }),
            this._parent && !e.onlySelf && this._parent._updateTouched(e);
        }
        markAsDirty(e = {}) {
          (this.pristine = !1),
            this._parent && !e.onlySelf && this._parent.markAsDirty(e);
        }
        markAsPristine(e = {}) {
          (this.pristine = !0),
            (this._pendingDirty = !1),
            this._forEachChild((t) => {
              t.markAsPristine({ onlySelf: !0 });
            }),
            this._parent && !e.onlySelf && this._parent._updatePristine(e);
        }
        markAsPending(e = {}) {
          (this.status = is),
            !1 !== e.emitEvent && this.statusChanges.emit(this.status),
            this._parent && !e.onlySelf && this._parent.markAsPending(e);
        }
        disable(e = {}) {
          const t = this._parentMarkedDirty(e.onlySelf);
          (this.status = Mo),
            (this.errors = null),
            this._forEachChild((i) => {
              i.disable(Object.assign(Object.assign({}, e), { onlySelf: !0 }));
            }),
            this._updateValue(),
            !1 !== e.emitEvent &&
              (this.valueChanges.emit(this.value),
              this.statusChanges.emit(this.status)),
            this._updateAncestors(
              Object.assign(Object.assign({}, e), { skipPristineCheck: t })
            ),
            this._onDisabledChange.forEach((i) => i(!0));
        }
        enable(e = {}) {
          const t = this._parentMarkedDirty(e.onlySelf);
          (this.status = Eo),
            this._forEachChild((i) => {
              i.enable(Object.assign(Object.assign({}, e), { onlySelf: !0 }));
            }),
            this.updateValueAndValidity({
              onlySelf: !0,
              emitEvent: e.emitEvent,
            }),
            this._updateAncestors(
              Object.assign(Object.assign({}, e), { skipPristineCheck: t })
            ),
            this._onDisabledChange.forEach((i) => i(!1));
        }
        _updateAncestors(e) {
          this._parent &&
            !e.onlySelf &&
            (this._parent.updateValueAndValidity(e),
            e.skipPristineCheck || this._parent._updatePristine(),
            this._parent._updateTouched());
        }
        setParent(e) {
          this._parent = e;
        }
        updateValueAndValidity(e = {}) {
          this._setInitialStatus(),
            this._updateValue(),
            this.enabled &&
              (this._cancelExistingSubscription(),
              (this.errors = this._runValidator()),
              (this.status = this._calculateStatus()),
              (this.status === Eo || this.status === is) &&
                this._runAsyncValidator(e.emitEvent)),
            !1 !== e.emitEvent &&
              (this.valueChanges.emit(this.value),
              this.statusChanges.emit(this.status)),
            this._parent &&
              !e.onlySelf &&
              this._parent.updateValueAndValidity(e);
        }
        _updateTreeValidity(e = { emitEvent: !0 }) {
          this._forEachChild((t) => t._updateTreeValidity(e)),
            this.updateValueAndValidity({
              onlySelf: !0,
              emitEvent: e.emitEvent,
            });
        }
        _setInitialStatus() {
          this.status = this._allControlsDisabled() ? Mo : Eo;
        }
        _runValidator() {
          return this.validator ? this.validator(this) : null;
        }
        _runAsyncValidator(e) {
          if (this.asyncValidator) {
            (this.status = is), (this._hasOwnPendingAsyncValidator = !0);
            const t = RC(this.asyncValidator(this));
            this._asyncValidationSubscription = t.subscribe((i) => {
              (this._hasOwnPendingAsyncValidator = !1),
                this.setErrors(i, { emitEvent: e });
            });
          }
        }
        _cancelExistingSubscription() {
          this._asyncValidationSubscription &&
            (this._asyncValidationSubscription.unsubscribe(),
            (this._hasOwnPendingAsyncValidator = !1));
        }
        setErrors(e, t = {}) {
          (this.errors = e), this._updateControlsErrors(!1 !== t.emitEvent);
        }
        get(e) {
          return (function R1(n, e, t) {
            if (
              null == e ||
              (Array.isArray(e) || (e = e.split(t)),
              Array.isArray(e) && 0 === e.length)
            )
              return null;
            let i = n;
            return (
              e.forEach((r) => {
                i = $h(i)
                  ? i.controls.hasOwnProperty(r)
                    ? i.controls[r]
                    : null
                  : (((n) => n instanceof N1)(i) && i.at(r)) || null;
              }),
              i
            );
          })(this, e, ".");
        }
        getError(e, t) {
          const i = t ? this.get(t) : this;
          return i && i.errors ? i.errors[e] : null;
        }
        hasError(e, t) {
          return !!this.getError(e, t);
        }
        get root() {
          let e = this;
          for (; e._parent; ) e = e._parent;
          return e;
        }
        _updateControlsErrors(e) {
          (this.status = this._calculateStatus()),
            e && this.statusChanges.emit(this.status),
            this._parent && this._parent._updateControlsErrors(e);
        }
        _initObservables() {
          (this.valueChanges = new Q()), (this.statusChanges = new Q());
        }
        _calculateStatus() {
          return this._allControlsDisabled()
            ? Mo
            : this.errors
            ? Pl
            : this._hasOwnPendingAsyncValidator ||
              this._anyControlsHaveStatus(is)
            ? is
            : this._anyControlsHaveStatus(Pl)
            ? Pl
            : Eo;
        }
        _anyControlsHaveStatus(e) {
          return this._anyControls((t) => t.status === e);
        }
        _anyControlsDirty() {
          return this._anyControls((e) => e.dirty);
        }
        _anyControlsTouched() {
          return this._anyControls((e) => e.touched);
        }
        _updatePristine(e = {}) {
          (this.pristine = !this._anyControlsDirty()),
            this._parent && !e.onlySelf && this._parent._updatePristine(e);
        }
        _updateTouched(e = {}) {
          (this.touched = this._anyControlsTouched()),
            this._parent && !e.onlySelf && this._parent._updateTouched(e);
        }
        _isBoxedValue(e) {
          return (
            "object" == typeof e &&
            null !== e &&
            2 === Object.keys(e).length &&
            "value" in e &&
            "disabled" in e
          );
        }
        _registerOnCollectionChange(e) {
          this._onCollectionChange = e;
        }
        _setUpdateStrategy(e) {
          Uh(e) && null != e.updateOn && (this._updateOn = e.updateOn);
        }
        _parentMarkedDirty(e) {
          return (
            !e &&
            !(!this._parent || !this._parent.dirty) &&
            !this._parent._anyControlsDirty()
          );
        }
      }
      class rs extends zh {
        constructor(e = null, t, i) {
          super(jh(t), Hh(i, t)),
            (this._onChange = []),
            (this._pendingChange = !1),
            this._applyFormState(e),
            this._setUpdateStrategy(t),
            this._initObservables(),
            this.updateValueAndValidity({
              onlySelf: !0,
              emitEvent: !!this.asyncValidator,
            });
        }
        setValue(e, t = {}) {
          (this.value = this._pendingValue = e),
            this._onChange.length &&
              !1 !== t.emitModelToViewChange &&
              this._onChange.forEach((i) =>
                i(this.value, !1 !== t.emitViewToModelChange)
              ),
            this.updateValueAndValidity(t);
        }
        patchValue(e, t = {}) {
          this.setValue(e, t);
        }
        reset(e = null, t = {}) {
          this._applyFormState(e),
            this.markAsPristine(t),
            this.markAsUntouched(t),
            this.setValue(this.value, t),
            (this._pendingChange = !1);
        }
        _updateValue() {}
        _anyControls(e) {
          return !1;
        }
        _allControlsDisabled() {
          return this.disabled;
        }
        registerOnChange(e) {
          this._onChange.push(e);
        }
        _unregisterOnChange(e) {
          Rl(this._onChange, e);
        }
        registerOnDisabledChange(e) {
          this._onDisabledChange.push(e);
        }
        _unregisterOnDisabledChange(e) {
          Rl(this._onDisabledChange, e);
        }
        _forEachChild(e) {}
        _syncPendingControls() {
          return !(
            "submit" !== this.updateOn ||
            (this._pendingDirty && this.markAsDirty(),
            this._pendingTouched && this.markAsTouched(),
            !this._pendingChange) ||
            (this.setValue(this._pendingValue, {
              onlySelf: !0,
              emitModelToViewChange: !1,
            }),
            0)
          );
        }
        _applyFormState(e) {
          this._isBoxedValue(e)
            ? ((this.value = this._pendingValue = e.value),
              e.disabled
                ? this.disable({ onlySelf: !0, emitEvent: !1 })
                : this.enable({ onlySelf: !0, emitEvent: !1 }))
            : (this.value = this._pendingValue = e);
        }
      }
      class Gh extends zh {
        constructor(e, t, i) {
          super(jh(t), Hh(i, t)),
            (this.controls = e),
            this._initObservables(),
            this._setUpdateStrategy(t),
            this._setUpControls(),
            this.updateValueAndValidity({
              onlySelf: !0,
              emitEvent: !!this.asyncValidator,
            });
        }
        registerControl(e, t) {
          return this.controls[e]
            ? this.controls[e]
            : ((this.controls[e] = t),
              t.setParent(this),
              t._registerOnCollectionChange(this._onCollectionChange),
              t);
        }
        addControl(e, t, i = {}) {
          this.registerControl(e, t),
            this.updateValueAndValidity({ emitEvent: i.emitEvent }),
            this._onCollectionChange();
        }
        removeControl(e, t = {}) {
          this.controls[e] &&
            this.controls[e]._registerOnCollectionChange(() => {}),
            delete this.controls[e],
            this.updateValueAndValidity({ emitEvent: t.emitEvent }),
            this._onCollectionChange();
        }
        setControl(e, t, i = {}) {
          this.controls[e] &&
            this.controls[e]._registerOnCollectionChange(() => {}),
            delete this.controls[e],
            t && this.registerControl(e, t),
            this.updateValueAndValidity({ emitEvent: i.emitEvent }),
            this._onCollectionChange();
        }
        contains(e) {
          return this.controls.hasOwnProperty(e) && this.controls[e].enabled;
        }
        setValue(e, t = {}) {
          iw(this, e),
            Object.keys(e).forEach((i) => {
              nw(this, i),
                this.controls[i].setValue(e[i], {
                  onlySelf: !0,
                  emitEvent: t.emitEvent,
                });
            }),
            this.updateValueAndValidity(t);
        }
        patchValue(e, t = {}) {
          null != e &&
            (Object.keys(e).forEach((i) => {
              this.controls[i] &&
                this.controls[i].patchValue(e[i], {
                  onlySelf: !0,
                  emitEvent: t.emitEvent,
                });
            }),
            this.updateValueAndValidity(t));
        }
        reset(e = {}, t = {}) {
          this._forEachChild((i, r) => {
            i.reset(e[r], { onlySelf: !0, emitEvent: t.emitEvent });
          }),
            this._updatePristine(t),
            this._updateTouched(t),
            this.updateValueAndValidity(t);
        }
        getRawValue() {
          return this._reduceChildren({}, (e, t, i) => ((e[i] = tw(t)), e));
        }
        _syncPendingControls() {
          let e = this._reduceChildren(
            !1,
            (t, i) => !!i._syncPendingControls() || t
          );
          return e && this.updateValueAndValidity({ onlySelf: !0 }), e;
        }
        _forEachChild(e) {
          Object.keys(this.controls).forEach((t) => {
            const i = this.controls[t];
            i && e(i, t);
          });
        }
        _setUpControls() {
          this._forEachChild((e) => {
            e.setParent(this),
              e._registerOnCollectionChange(this._onCollectionChange);
          });
        }
        _updateValue() {
          this.value = this._reduceValue();
        }
        _anyControls(e) {
          for (const t of Object.keys(this.controls)) {
            const i = this.controls[t];
            if (this.contains(t) && e(i)) return !0;
          }
          return !1;
        }
        _reduceValue() {
          return this._reduceChildren(
            {},
            (e, t, i) => ((t.enabled || this.disabled) && (e[i] = t.value), e)
          );
        }
        _reduceChildren(e, t) {
          let i = e;
          return (
            this._forEachChild((r, s) => {
              i = t(i, r, s);
            }),
            i
          );
        }
        _allControlsDisabled() {
          for (const e of Object.keys(this.controls))
            if (this.controls[e].enabled) return !1;
          return Object.keys(this.controls).length > 0 || this.disabled;
        }
      }
      class N1 extends zh {
        constructor(e, t, i) {
          super(jh(t), Hh(i, t)),
            (this.controls = e),
            this._initObservables(),
            this._setUpdateStrategy(t),
            this._setUpControls(),
            this.updateValueAndValidity({
              onlySelf: !0,
              emitEvent: !!this.asyncValidator,
            });
        }
        at(e) {
          return this.controls[e];
        }
        push(e, t = {}) {
          this.controls.push(e),
            this._registerControl(e),
            this.updateValueAndValidity({ emitEvent: t.emitEvent }),
            this._onCollectionChange();
        }
        insert(e, t, i = {}) {
          this.controls.splice(e, 0, t),
            this._registerControl(t),
            this.updateValueAndValidity({ emitEvent: i.emitEvent });
        }
        removeAt(e, t = {}) {
          this.controls[e] &&
            this.controls[e]._registerOnCollectionChange(() => {}),
            this.controls.splice(e, 1),
            this.updateValueAndValidity({ emitEvent: t.emitEvent });
        }
        setControl(e, t, i = {}) {
          this.controls[e] &&
            this.controls[e]._registerOnCollectionChange(() => {}),
            this.controls.splice(e, 1),
            t && (this.controls.splice(e, 0, t), this._registerControl(t)),
            this.updateValueAndValidity({ emitEvent: i.emitEvent }),
            this._onCollectionChange();
        }
        get length() {
          return this.controls.length;
        }
        setValue(e, t = {}) {
          iw(this, e),
            e.forEach((i, r) => {
              nw(this, r),
                this.at(r).setValue(i, {
                  onlySelf: !0,
                  emitEvent: t.emitEvent,
                });
            }),
            this.updateValueAndValidity(t);
        }
        patchValue(e, t = {}) {
          null != e &&
            (e.forEach((i, r) => {
              this.at(r) &&
                this.at(r).patchValue(i, {
                  onlySelf: !0,
                  emitEvent: t.emitEvent,
                });
            }),
            this.updateValueAndValidity(t));
        }
        reset(e = [], t = {}) {
          this._forEachChild((i, r) => {
            i.reset(e[r], { onlySelf: !0, emitEvent: t.emitEvent });
          }),
            this._updatePristine(t),
            this._updateTouched(t),
            this.updateValueAndValidity(t);
        }
        getRawValue() {
          return this.controls.map((e) => tw(e));
        }
        clear(e = {}) {
          this.controls.length < 1 ||
            (this._forEachChild((t) => t._registerOnCollectionChange(() => {})),
            this.controls.splice(0),
            this.updateValueAndValidity({ emitEvent: e.emitEvent }));
        }
        _syncPendingControls() {
          let e = this.controls.reduce(
            (t, i) => !!i._syncPendingControls() || t,
            !1
          );
          return e && this.updateValueAndValidity({ onlySelf: !0 }), e;
        }
        _forEachChild(e) {
          this.controls.forEach((t, i) => {
            e(t, i);
          });
        }
        _updateValue() {
          this.value = this.controls
            .filter((e) => e.enabled || this.disabled)
            .map((e) => e.value);
        }
        _anyControls(e) {
          return this.controls.some((t) => t.enabled && e(t));
        }
        _setUpControls() {
          this._forEachChild((e) => this._registerControl(e));
        }
        _allControlsDisabled() {
          for (const e of this.controls) if (e.enabled) return !1;
          return this.controls.length > 0 || this.disabled;
        }
        _registerControl(e) {
          e.setParent(this),
            e._registerOnCollectionChange(this._onCollectionChange);
        }
      }
      const L1 = { provide: vt, useExisting: _e(() => Ao) },
        So = (() => Promise.resolve(null))();
      let Ao = (() => {
        class n extends vt {
          constructor(t, i) {
            super(),
              (this.submitted = !1),
              (this._directives = []),
              (this.ngSubmit = new Q()),
              (this.form = new Gh({}, xh(t), kh(i)));
          }
          ngAfterViewInit() {
            this._setUpdateStrategy();
          }
          get formDirective() {
            return this;
          }
          get control() {
            return this.form;
          }
          get path() {
            return [];
          }
          get controls() {
            return this.form.controls;
          }
          addControl(t) {
            So.then(() => {
              const i = this._findContainer(t.path);
              (t.control = i.registerControl(t.name, t.control)),
                Do(t.control, t),
                t.control.updateValueAndValidity({ emitEvent: !1 }),
                this._directives.push(t);
            });
          }
          getControl(t) {
            return this.form.get(t.path);
          }
          removeControl(t) {
            So.then(() => {
              const i = this._findContainer(t.path);
              i && i.removeControl(t.name), Rl(this._directives, t);
            });
          }
          addFormGroup(t) {
            So.then(() => {
              const i = this._findContainer(t.path),
                r = new Gh({});
              ZC(r, t),
                i.registerControl(t.name, r),
                r.updateValueAndValidity({ emitEvent: !1 });
            });
          }
          removeFormGroup(t) {
            So.then(() => {
              const i = this._findContainer(t.path);
              i && i.removeControl(t.name);
            });
          }
          getFormGroup(t) {
            return this.form.get(t.path);
          }
          updateModel(t, i) {
            So.then(() => {
              this.form.get(t.path).setValue(i);
            });
          }
          setValue(t) {
            this.control.setValue(t);
          }
          onSubmit(t) {
            return (
              (this.submitted = !0),
              QC(this.form, this._directives),
              this.ngSubmit.emit(t),
              !1
            );
          }
          onReset() {
            this.resetForm();
          }
          resetForm(t) {
            this.form.reset(t), (this.submitted = !1);
          }
          _setUpdateStrategy() {
            this.options &&
              null != this.options.updateOn &&
              (this.form._updateOn = this.options.updateOn);
          }
          _findContainer(t) {
            return t.pop(), t.length ? this.form.get(t) : this.form;
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(_(dt, 10), _(wi, 10));
          }),
          (n.ɵdir = x({
            type: n,
            selectors: [
              ["form", 3, "ngNoForm", "", 3, "formGroup", ""],
              ["ng-form"],
              ["", "ngForm", ""],
            ],
            hostBindings: function (t, i) {
              1 & t &&
                Z("submit", function (s) {
                  return i.onSubmit(s);
                })("reset", function () {
                  return i.onReset();
                });
            },
            inputs: { options: ["ngFormOptions", "options"] },
            outputs: { ngSubmit: "ngSubmit" },
            exportAs: ["ngForm"],
            features: [ge([L1]), se],
          })),
          n
        );
      })();
      const H1 = { provide: vn, useExisting: _e(() => qh), multi: !0 };
      let qh = (() => {
          class n extends Wi {
            writeValue(t) {
              this.setProperty("value", null == t ? "" : t);
            }
            registerOnChange(t) {
              this.onChange = (i) => {
                t("" == i ? null : parseFloat(i));
              };
            }
          }
          return (
            (n.ɵfac = (function () {
              let e;
              return function (i) {
                return (e || (e = gt(n)))(i || n);
              };
            })()),
            (n.ɵdir = x({
              type: n,
              selectors: [
                ["input", "type", "number", "formControlName", ""],
                ["input", "type", "number", "formControl", ""],
                ["input", "type", "number", "ngModel", ""],
              ],
              hostBindings: function (t, i) {
                1 & t &&
                  Z("input", function (s) {
                    return i.onChange(s.target.value);
                  })("blur", function () {
                    return i.onTouched();
                  });
              },
              features: [ge([H1]), se],
            })),
            n
          );
        })(),
        lw = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({})),
            n
          );
        })();
      const Wh = new T("NgModelWithFormControlWarning"),
        G1 = { provide: Nn, useExisting: _e(() => Kh) };
      let Kh = (() => {
        class n extends Nn {
          constructor(t, i, r, s) {
            super(),
              (this._ngModelWarningConfig = s),
              (this.update = new Q()),
              (this._ngModelWarningSent = !1),
              this._setValidators(t),
              this._setAsyncValidators(i),
              (this.valueAccessor = (function Vh(n, e) {
                if (!e) return null;
                let t, i, r;
                return (
                  Array.isArray(e),
                  e.forEach((s) => {
                    s.constructor === Sl
                      ? (t = s)
                      : (function F1(n) {
                          return Object.getPrototypeOf(n.constructor) === Wi;
                        })(s)
                      ? (i = s)
                      : (r = s);
                  }),
                  r || i || t || null
                );
              })(0, r));
          }
          set isDisabled(t) {}
          ngOnChanges(t) {
            if (this._isControlChanged(t)) {
              const i = t.form.previousValue;
              i && xl(i, this, !1),
                Do(this.form, this),
                this.control.disabled &&
                  this.valueAccessor.setDisabledState &&
                  this.valueAccessor.setDisabledState(!0),
                this.form.updateValueAndValidity({ emitEvent: !1 });
            }
            (function Lh(n, e) {
              if (!n.hasOwnProperty("model")) return !1;
              const t = n.model;
              return !!t.isFirstChange() || !Object.is(e, t.currentValue);
            })(t, this.viewModel) &&
              (this.form.setValue(this.model), (this.viewModel = this.model));
          }
          ngOnDestroy() {
            this.form && xl(this.form, this, !1);
          }
          get path() {
            return [];
          }
          get control() {
            return this.form;
          }
          viewToModelUpdate(t) {
            (this.viewModel = t), this.update.emit(t);
          }
          _isControlChanged(t) {
            return t.hasOwnProperty("form");
          }
        }
        return (
          (n._ngModelWarningSentOnce = !1),
          (n.ɵfac = function (t) {
            return new (t || n)(_(dt, 10), _(wi, 10), _(vn, 10), _(Wh, 8));
          }),
          (n.ɵdir = x({
            type: n,
            selectors: [["", "formControl", ""]],
            inputs: {
              form: ["formControl", "form"],
              isDisabled: ["disabled", "isDisabled"],
              model: ["ngModel", "model"],
            },
            outputs: { update: "ngModelChange" },
            exportAs: ["ngForm"],
            features: [ge([G1]), se, at],
          })),
          n
        );
      })();
      const q1 = { provide: vt, useExisting: _e(() => To) };
      let To = (() => {
          class n extends vt {
            constructor(t, i) {
              super(),
                (this.validators = t),
                (this.asyncValidators = i),
                (this.submitted = !1),
                (this._onCollectionChange = () => this._updateDomValue()),
                (this.directives = []),
                (this.form = null),
                (this.ngSubmit = new Q()),
                this._setValidators(t),
                this._setAsyncValidators(i);
            }
            ngOnChanges(t) {
              this._checkFormPresent(),
                t.hasOwnProperty("form") &&
                  (this._updateValidators(),
                  this._updateDomValue(),
                  this._updateRegistrations(),
                  (this._oldForm = this.form));
            }
            ngOnDestroy() {
              this.form &&
                (Fl(this.form, this),
                this.form._onCollectionChange === this._onCollectionChange &&
                  this.form._registerOnCollectionChange(() => {}));
            }
            get formDirective() {
              return this;
            }
            get control() {
              return this.form;
            }
            get path() {
              return [];
            }
            addControl(t) {
              const i = this.form.get(t.path);
              return (
                Do(i, t),
                i.updateValueAndValidity({ emitEvent: !1 }),
                this.directives.push(t),
                i
              );
            }
            getControl(t) {
              return this.form.get(t.path);
            }
            removeControl(t) {
              xl(t.control || null, t, !1), Rl(this.directives, t);
            }
            addFormGroup(t) {
              this._setUpFormContainer(t);
            }
            removeFormGroup(t) {
              this._cleanUpFormContainer(t);
            }
            getFormGroup(t) {
              return this.form.get(t.path);
            }
            addFormArray(t) {
              this._setUpFormContainer(t);
            }
            removeFormArray(t) {
              this._cleanUpFormContainer(t);
            }
            getFormArray(t) {
              return this.form.get(t.path);
            }
            updateModel(t, i) {
              this.form.get(t.path).setValue(i);
            }
            onSubmit(t) {
              return (
                (this.submitted = !0),
                QC(this.form, this.directives),
                this.ngSubmit.emit(t),
                !1
              );
            }
            onReset() {
              this.resetForm();
            }
            resetForm(t) {
              this.form.reset(t), (this.submitted = !1);
            }
            _updateDomValue() {
              this.directives.forEach((t) => {
                const i = t.control,
                  r = this.form.get(t.path);
                i !== r &&
                  (xl(i || null, t), ew(r) && (Do(r, t), (t.control = r)));
              }),
                this.form._updateTreeValidity({ emitEvent: !1 });
            }
            _setUpFormContainer(t) {
              const i = this.form.get(t.path);
              ZC(i, t), i.updateValueAndValidity({ emitEvent: !1 });
            }
            _cleanUpFormContainer(t) {
              if (this.form) {
                const i = this.form.get(t.path);
                i &&
                  (function x1(n, e) {
                    return Fl(n, e);
                  })(i, t) &&
                  i.updateValueAndValidity({ emitEvent: !1 });
              }
            }
            _updateRegistrations() {
              this.form._registerOnCollectionChange(this._onCollectionChange),
                this._oldForm &&
                  this._oldForm._registerOnCollectionChange(() => {});
            }
            _updateValidators() {
              Nh(this.form, this), this._oldForm && Fl(this._oldForm, this);
            }
            _checkFormPresent() {}
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(dt, 10), _(wi, 10));
            }),
            (n.ɵdir = x({
              type: n,
              selectors: [["", "formGroup", ""]],
              hostBindings: function (t, i) {
                1 & t &&
                  Z("submit", function (s) {
                    return i.onSubmit(s);
                  })("reset", function () {
                    return i.onReset();
                  });
              },
              inputs: { form: ["formGroup", "form"] },
              outputs: { ngSubmit: "ngSubmit" },
              exportAs: ["ngForm"],
              features: [ge([q1]), se, at],
            })),
            n
          );
        })(),
        Ew = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({ imports: [[lw]] })),
            n
          );
        })(),
        uN = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({ imports: [Ew] })),
            n
          );
        })(),
        dN = (() => {
          class n {
            static withConfig(t) {
              return {
                ngModule: n,
                providers: [
                  { provide: Wh, useValue: t.warnOnNgModelWithFormControl },
                ],
              };
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({ imports: [Ew] })),
            n
          );
        })();
      const hN = new T("cdk-dir-doc", {
          providedIn: "root",
          factory: function fN() {
            return Xg(ue);
          },
        }),
        pN =
          /^(ar|ckb|dv|he|iw|fa|nqo|ps|sd|ug|ur|yi|.*[-_](Adlm|Arab|Hebr|Nkoo|Rohg|Thaa))(?!.*[-_](Latn|Cyrl)($|-|_))($|-|_)/i;
      let ef,
        Nl = (() => {
          class n {
            constructor(t) {
              if (((this.value = "ltr"), (this.change = new Q()), t)) {
                const r = t.documentElement ? t.documentElement.dir : null;
                this.value = (function gN(n) {
                  const e = (null == n ? void 0 : n.toLowerCase()) || "";
                  return "auto" === e &&
                    "undefined" != typeof navigator &&
                    (null == navigator ? void 0 : navigator.language)
                    ? pN.test(navigator.language)
                      ? "rtl"
                      : "ltr"
                    : "rtl" === e
                    ? "rtl"
                    : "ltr";
                })((t.body ? t.body.dir : null) || r || "ltr");
              }
            }
            ngOnDestroy() {
              this.change.complete();
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(hN, 8));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
            n
          );
        })(),
        Io = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({})),
            n
          );
        })();
      try {
        ef = "undefined" != typeof Intl && Intl.v8BreakIterator;
      } catch (n) {
        ef = !1;
      }
      let ss,
        Jt = (() => {
          class n {
            constructor(t) {
              (this._platformId = t),
                (this.isBrowser = this._platformId
                  ? (function bP(n) {
                      return n === nC;
                    })(this._platformId)
                  : "object" == typeof document && !!document),
                (this.EDGE =
                  this.isBrowser && /(edge)/i.test(navigator.userAgent)),
                (this.TRIDENT =
                  this.isBrowser &&
                  /(msie|trident)/i.test(navigator.userAgent)),
                (this.BLINK =
                  this.isBrowser &&
                  !(!window.chrome && !ef) &&
                  "undefined" != typeof CSS &&
                  !this.EDGE &&
                  !this.TRIDENT),
                (this.WEBKIT =
                  this.isBrowser &&
                  /AppleWebKit/i.test(navigator.userAgent) &&
                  !this.BLINK &&
                  !this.EDGE &&
                  !this.TRIDENT),
                (this.IOS =
                  this.isBrowser &&
                  /iPad|iPhone|iPod/.test(navigator.userAgent) &&
                  !("MSStream" in window)),
                (this.FIREFOX =
                  this.isBrowser &&
                  /(firefox|minefield)/i.test(navigator.userAgent)),
                (this.ANDROID =
                  this.isBrowser &&
                  /android/i.test(navigator.userAgent) &&
                  !this.TRIDENT),
                (this.SAFARI =
                  this.isBrowser &&
                  /safari/i.test(navigator.userAgent) &&
                  this.WEBKIT);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(go));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
            n
          );
        })();
      const Sw = [
        "color",
        "button",
        "checkbox",
        "date",
        "datetime-local",
        "email",
        "file",
        "hidden",
        "image",
        "month",
        "number",
        "password",
        "radio",
        "range",
        "reset",
        "search",
        "submit",
        "tel",
        "text",
        "time",
        "url",
        "week",
      ];
      function Aw() {
        if (ss) return ss;
        if ("object" != typeof document || !document)
          return (ss = new Set(Sw)), ss;
        let n = document.createElement("input");
        return (
          (ss = new Set(
            Sw.filter((e) => (n.setAttribute("type", e), n.type === e))
          )),
          ss
        );
      }
      let xo, Ki, tf;
      function Ll(n) {
        return (function mN() {
          if (null == xo && "undefined" != typeof window)
            try {
              window.addEventListener(
                "test",
                null,
                Object.defineProperty({}, "passive", { get: () => (xo = !0) })
              );
            } finally {
              xo = xo || !1;
            }
          return xo;
        })()
          ? n
          : !!n.capture;
      }
      function _N() {
        if (null == Ki) {
          if (
            "object" != typeof document ||
            !document ||
            "function" != typeof Element ||
            !Element
          )
            return (Ki = !1), Ki;
          if ("scrollBehavior" in document.documentElement.style) Ki = !0;
          else {
            const n = Element.prototype.scrollTo;
            Ki = !!n && !/\{\s*\[native code\]\s*\}/.test(n.toString());
          }
        }
        return Ki;
      }
      function Yi(n) {
        return n.composedPath ? n.composedPath()[0] : n.target;
      }
      function nf() {
        return (
          ("undefined" != typeof __karma__ && !!__karma__) ||
          ("undefined" != typeof jasmine && !!jasmine) ||
          ("undefined" != typeof jest && !!jest) ||
          ("undefined" != typeof Mocha && !!Mocha)
        );
      }
      class en extends le {
        constructor(e) {
          super(), (this._value = e);
        }
        get value() {
          return this.getValue();
        }
        _subscribe(e) {
          const t = super._subscribe(e);
          return !t.closed && e.next(this._value), t;
        }
        getValue() {
          const { hasError: e, thrownError: t, _value: i } = this;
          if (e) throw t;
          return this._throwIfClosed(), i;
        }
        next(e) {
          super.next((this._value = e));
        }
      }
      function H(...n) {
        return et(n, Es(n));
      }
      function ko(n, ...e) {
        return e.length
          ? e.some((t) => n[t])
          : n.altKey || n.shiftKey || n.ctrlKey || n.metaKey;
      }
      function Mt(n, e, t) {
        const i = ae(n) || e || t ? { next: n, error: e, complete: t } : n;
        return i
          ? Fe((r, s) => {
              var o;
              null === (o = i.subscribe) || void 0 === o || o.call(i);
              let a = !0;
              r.subscribe(
                new De(
                  s,
                  (l) => {
                    var c;
                    null === (c = i.next) || void 0 === c || c.call(i, l),
                      s.next(l);
                  },
                  () => {
                    var l;
                    (a = !1),
                      null === (l = i.complete) || void 0 === l || l.call(i),
                      s.complete();
                  },
                  (l) => {
                    var c;
                    (a = !1),
                      null === (c = i.error) || void 0 === c || c.call(i, l),
                      s.error(l);
                  },
                  () => {
                    var l, c;
                    a &&
                      (null === (l = i.unsubscribe) ||
                        void 0 === l ||
                        l.call(i)),
                      null === (c = i.finalize) || void 0 === c || c.call(i);
                  }
                )
              );
            })
          : ai;
      }
      class kN extends Le {
        constructor(e, t) {
          super();
        }
        schedule(e, t = 0) {
          return this;
        }
      }
      const Bl = {
        setInterval(...n) {
          const { delegate: e } = Bl;
          return ((null == e ? void 0 : e.setInterval) || setInterval)(...n);
        },
        clearInterval(n) {
          const { delegate: e } = Bl;
          return ((null == e ? void 0 : e.clearInterval) || clearInterval)(n);
        },
        delegate: void 0,
      };
      class cf extends kN {
        constructor(e, t) {
          super(e, t),
            (this.scheduler = e),
            (this.work = t),
            (this.pending = !1);
        }
        schedule(e, t = 0) {
          if (this.closed) return this;
          this.state = e;
          const i = this.id,
            r = this.scheduler;
          return (
            null != i && (this.id = this.recycleAsyncId(r, i, t)),
            (this.pending = !0),
            (this.delay = t),
            (this.id = this.id || this.requestAsyncId(r, this.id, t)),
            this
          );
        }
        requestAsyncId(e, t, i = 0) {
          return Bl.setInterval(e.flush.bind(e, this), i);
        }
        recycleAsyncId(e, t, i = 0) {
          if (null != i && this.delay === i && !1 === this.pending) return t;
          Bl.clearInterval(t);
        }
        execute(e, t) {
          if (this.closed) return new Error("executing a cancelled action");
          this.pending = !1;
          const i = this._execute(e, t);
          if (i) return i;
          !1 === this.pending &&
            null != this.id &&
            (this.id = this.recycleAsyncId(this.scheduler, this.id, null));
        }
        _execute(e, t) {
          let r,
            i = !1;
          try {
            this.work(e);
          } catch (s) {
            (i = !0),
              (r = s || new Error("Scheduled action threw falsy error"));
          }
          if (i) return this.unsubscribe(), r;
        }
        unsubscribe() {
          if (!this.closed) {
            const { id: e, scheduler: t } = this,
              { actions: i } = t;
            (this.work = this.state = this.scheduler = null),
              (this.pending = !1),
              ar(i, this),
              null != e && (this.id = this.recycleAsyncId(t, e, null)),
              (this.delay = null),
              super.unsubscribe();
          }
        }
      }
      const xw = { now: () => (xw.delegate || Date).now(), delegate: void 0 };
      class Fo {
        constructor(e, t = Fo.now) {
          (this.schedulerActionCtor = e), (this.now = t);
        }
        schedule(e, t = 0, i) {
          return new this.schedulerActionCtor(this, e).schedule(i, t);
        }
      }
      Fo.now = xw.now;
      class uf extends Fo {
        constructor(e, t = Fo.now) {
          super(e, t),
            (this.actions = []),
            (this._active = !1),
            (this._scheduled = void 0);
        }
        flush(e) {
          const { actions: t } = this;
          if (this._active) return void t.push(e);
          let i;
          this._active = !0;
          do {
            if ((i = e.execute(e.state, e.delay))) break;
          } while ((e = t.shift()));
          if (((this._active = !1), i)) {
            for (; (e = t.shift()); ) e.unsubscribe();
            throw i;
          }
        }
      }
      const kw = new uf(cf),
        Fw = kw;
      function Rw(n, e = kw) {
        return Fe((t, i) => {
          let r = null,
            s = null,
            o = null;
          const a = () => {
            if (r) {
              r.unsubscribe(), (r = null);
              const c = s;
              (s = null), i.next(c);
            }
          };
          function l() {
            const c = o + n,
              u = e.now();
            if (u < c) return (r = this.schedule(void 0, c - u)), void i.add(r);
            a();
          }
          t.subscribe(
            new De(
              i,
              (c) => {
                (s = c), (o = e.now()), r || ((r = e.schedule(l, n)), i.add(r));
              },
              () => {
                a(), i.complete();
              },
              void 0,
              () => {
                s = r = null;
              }
            )
          );
        });
      }
      function tn(n, e) {
        return Fe((t, i) => {
          let r = 0;
          t.subscribe(new De(i, (s) => n.call(e, s, r++) && i.next(s)));
        });
      }
      function Pw(n, e = ai) {
        return (
          (n = null != n ? n : RN),
          Fe((t, i) => {
            let r,
              s = !0;
            t.subscribe(
              new De(i, (o) => {
                const a = e(o);
                (s || !n(r, a)) && ((s = !1), (r = a), i.next(o));
              })
            );
          })
        );
      }
      function RN(n, e) {
        return n === e;
      }
      function Nt(n) {
        return Fe((e, t) => {
          St(n).subscribe(new De(t, () => t.complete(), ws)),
            !t.closed && e.subscribe(t);
        });
      }
      class VN extends class LN {
        constructor(e) {
          (this._items = e),
            (this._activeItemIndex = -1),
            (this._activeItem = null),
            (this._wrap = !1),
            (this._letterKeyStream = new le()),
            (this._typeaheadSubscription = Le.EMPTY),
            (this._vertical = !0),
            (this._allowedModifierKeys = []),
            (this._homeAndEnd = !1),
            (this._skipPredicateFn = (t) => t.disabled),
            (this._pressedLetters = []),
            (this.tabOut = new le()),
            (this.change = new le()),
            e instanceof ho &&
              e.changes.subscribe((t) => {
                if (this._activeItem) {
                  const r = t.toArray().indexOf(this._activeItem);
                  r > -1 &&
                    r !== this._activeItemIndex &&
                    (this._activeItemIndex = r);
                }
              });
        }
        skipPredicate(e) {
          return (this._skipPredicateFn = e), this;
        }
        withWrap(e = !0) {
          return (this._wrap = e), this;
        }
        withVerticalOrientation(e = !0) {
          return (this._vertical = e), this;
        }
        withHorizontalOrientation(e) {
          return (this._horizontal = e), this;
        }
        withAllowedModifierKeys(e) {
          return (this._allowedModifierKeys = e), this;
        }
        withTypeAhead(e = 200) {
          return (
            this._typeaheadSubscription.unsubscribe(),
            (this._typeaheadSubscription = this._letterKeyStream
              .pipe(
                Mt((t) => this._pressedLetters.push(t)),
                Rw(e),
                tn(() => this._pressedLetters.length > 0),
                re(() => this._pressedLetters.join(""))
              )
              .subscribe((t) => {
                const i = this._getItemsArray();
                for (let r = 1; r < i.length + 1; r++) {
                  const s = (this._activeItemIndex + r) % i.length,
                    o = i[s];
                  if (
                    !this._skipPredicateFn(o) &&
                    0 === o.getLabel().toUpperCase().trim().indexOf(t)
                  ) {
                    this.setActiveItem(s);
                    break;
                  }
                }
                this._pressedLetters = [];
              })),
            this
          );
        }
        withHomeAndEnd(e = !0) {
          return (this._homeAndEnd = e), this;
        }
        setActiveItem(e) {
          const t = this._activeItem;
          this.updateActiveItem(e),
            this._activeItem !== t && this.change.next(this._activeItemIndex);
        }
        onKeydown(e) {
          const t = e.keyCode,
            r = ["altKey", "ctrlKey", "metaKey", "shiftKey"].every(
              (s) => !e[s] || this._allowedModifierKeys.indexOf(s) > -1
            );
          switch (t) {
            case 9:
              return void this.tabOut.next();
            case 40:
              if (this._vertical && r) {
                this.setNextItemActive();
                break;
              }
              return;
            case 38:
              if (this._vertical && r) {
                this.setPreviousItemActive();
                break;
              }
              return;
            case 39:
              if (this._horizontal && r) {
                "rtl" === this._horizontal
                  ? this.setPreviousItemActive()
                  : this.setNextItemActive();
                break;
              }
              return;
            case 37:
              if (this._horizontal && r) {
                "rtl" === this._horizontal
                  ? this.setNextItemActive()
                  : this.setPreviousItemActive();
                break;
              }
              return;
            case 36:
              if (this._homeAndEnd && r) {
                this.setFirstItemActive();
                break;
              }
              return;
            case 35:
              if (this._homeAndEnd && r) {
                this.setLastItemActive();
                break;
              }
              return;
            default:
              return void (
                (r || ko(e, "shiftKey")) &&
                (e.key && 1 === e.key.length
                  ? this._letterKeyStream.next(e.key.toLocaleUpperCase())
                  : ((t >= 65 && t <= 90) || (t >= 48 && t <= 57)) &&
                    this._letterKeyStream.next(String.fromCharCode(t)))
              );
          }
          (this._pressedLetters = []), e.preventDefault();
        }
        get activeItemIndex() {
          return this._activeItemIndex;
        }
        get activeItem() {
          return this._activeItem;
        }
        isTyping() {
          return this._pressedLetters.length > 0;
        }
        setFirstItemActive() {
          this._setActiveItemByIndex(0, 1);
        }
        setLastItemActive() {
          this._setActiveItemByIndex(this._items.length - 1, -1);
        }
        setNextItemActive() {
          this._activeItemIndex < 0
            ? this.setFirstItemActive()
            : this._setActiveItemByDelta(1);
        }
        setPreviousItemActive() {
          this._activeItemIndex < 0 && this._wrap
            ? this.setLastItemActive()
            : this._setActiveItemByDelta(-1);
        }
        updateActiveItem(e) {
          const t = this._getItemsArray(),
            i = "number" == typeof e ? e : t.indexOf(e),
            r = t[i];
          (this._activeItem = null == r ? null : r),
            (this._activeItemIndex = i);
        }
        _setActiveItemByDelta(e) {
          this._wrap
            ? this._setActiveInWrapMode(e)
            : this._setActiveInDefaultMode(e);
        }
        _setActiveInWrapMode(e) {
          const t = this._getItemsArray();
          for (let i = 1; i <= t.length; i++) {
            const r = (this._activeItemIndex + e * i + t.length) % t.length;
            if (!this._skipPredicateFn(t[r])) return void this.setActiveItem(r);
          }
        }
        _setActiveInDefaultMode(e) {
          this._setActiveItemByIndex(this._activeItemIndex + e, e);
        }
        _setActiveItemByIndex(e, t) {
          const i = this._getItemsArray();
          if (i[e]) {
            for (; this._skipPredicateFn(i[e]); ) if (!i[(e += t)]) return;
            this.setActiveItem(e);
          }
        }
        _getItemsArray() {
          return this._items instanceof ho
            ? this._items.toArray()
            : this._items;
        }
      } {
        setActiveItem(e) {
          this.activeItem && this.activeItem.setInactiveStyles(),
            super.setActiveItem(e),
            this.activeItem && this.activeItem.setActiveStyles();
        }
      }
      function Bw(n) {
        return 0 === n.buttons || (0 === n.offsetX && 0 === n.offsetY);
      }
      function jw(n) {
        const e =
          (n.touches && n.touches[0]) ||
          (n.changedTouches && n.changedTouches[0]);
        return !(
          !e ||
          -1 !== e.identifier ||
          (null != e.radiusX && 1 !== e.radiusX) ||
          (null != e.radiusY && 1 !== e.radiusY)
        );
      }
      const zN = new T("cdk-input-modality-detector-options"),
        GN = { ignoreKeys: [18, 17, 224, 91, 16] },
        os = Ll({ passive: !0, capture: !0 });
      let qN = (() => {
        class n {
          constructor(t, i, r, s) {
            (this._platform = t),
              (this._mostRecentTarget = null),
              (this._modality = new en(null)),
              (this._lastTouchMs = 0),
              (this._onKeydown = (o) => {
                var a, l;
                (null ===
                  (l =
                    null === (a = this._options) || void 0 === a
                      ? void 0
                      : a.ignoreKeys) || void 0 === l
                  ? void 0
                  : l.some((c) => c === o.keyCode)) ||
                  (this._modality.next("keyboard"),
                  (this._mostRecentTarget = Yi(o)));
              }),
              (this._onMousedown = (o) => {
                Date.now() - this._lastTouchMs < 650 ||
                  (this._modality.next(Bw(o) ? "keyboard" : "mouse"),
                  (this._mostRecentTarget = Yi(o)));
              }),
              (this._onTouchstart = (o) => {
                jw(o)
                  ? this._modality.next("keyboard")
                  : ((this._lastTouchMs = Date.now()),
                    this._modality.next("touch"),
                    (this._mostRecentTarget = Yi(o)));
              }),
              (this._options = Object.assign(Object.assign({}, GN), s)),
              (this.modalityDetected = this._modality.pipe(
                (function FN(n) {
                  return tn((e, t) => n <= t);
                })(1)
              )),
              (this.modalityChanged = this.modalityDetected.pipe(Pw())),
              t.isBrowser &&
                i.runOutsideAngular(() => {
                  r.addEventListener("keydown", this._onKeydown, os),
                    r.addEventListener("mousedown", this._onMousedown, os),
                    r.addEventListener("touchstart", this._onTouchstart, os);
                });
          }
          get mostRecentModality() {
            return this._modality.value;
          }
          ngOnDestroy() {
            this._modality.complete(),
              this._platform.isBrowser &&
                (document.removeEventListener("keydown", this._onKeydown, os),
                document.removeEventListener(
                  "mousedown",
                  this._onMousedown,
                  os
                ),
                document.removeEventListener(
                  "touchstart",
                  this._onTouchstart,
                  os
                ));
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(Jt), b(ee), b(ue), b(zN, 8));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
          n
        );
      })();
      const WN = new T("liveAnnouncerElement", {
          providedIn: "root",
          factory: function KN() {
            return null;
          },
        }),
        YN = new T("LIVE_ANNOUNCER_DEFAULT_OPTIONS");
      let ZN = (() => {
        class n {
          constructor(t, i, r, s) {
            (this._ngZone = i),
              (this._defaultOptions = s),
              (this._document = r),
              (this._liveElement = t || this._createLiveElement());
          }
          announce(t, ...i) {
            const r = this._defaultOptions;
            let s, o;
            return (
              1 === i.length && "number" == typeof i[0]
                ? (o = i[0])
                : ([s, o] = i),
              this.clear(),
              clearTimeout(this._previousTimeout),
              s || (s = r && r.politeness ? r.politeness : "polite"),
              null == o && r && (o = r.duration),
              this._liveElement.setAttribute("aria-live", s),
              this._ngZone.runOutsideAngular(
                () => (
                  this._currentPromise ||
                    (this._currentPromise = new Promise(
                      (a) => (this._currentResolve = a)
                    )),
                  clearTimeout(this._previousTimeout),
                  (this._previousTimeout = setTimeout(() => {
                    (this._liveElement.textContent = t),
                      "number" == typeof o &&
                        (this._previousTimeout = setTimeout(
                          () => this.clear(),
                          o
                        )),
                      this._currentResolve(),
                      (this._currentPromise = this._currentResolve = void 0);
                  }, 100)),
                  this._currentPromise
                )
              )
            );
          }
          clear() {
            this._liveElement && (this._liveElement.textContent = "");
          }
          ngOnDestroy() {
            var t, i;
            clearTimeout(this._previousTimeout),
              null === (t = this._liveElement) || void 0 === t || t.remove(),
              (this._liveElement = null),
              null === (i = this._currentResolve) ||
                void 0 === i ||
                i.call(this),
              (this._currentPromise = this._currentResolve = void 0);
          }
          _createLiveElement() {
            const t = "cdk-live-announcer-element",
              i = this._document.getElementsByClassName(t),
              r = this._document.createElement("div");
            for (let s = 0; s < i.length; s++) i[s].remove();
            return (
              r.classList.add(t),
              r.classList.add("cdk-visually-hidden"),
              r.setAttribute("aria-atomic", "true"),
              r.setAttribute("aria-live", "polite"),
              this._document.body.appendChild(r),
              r
            );
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(WN, 8), b(ee), b(ue), b(YN, 8));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
          n
        );
      })();
      const QN = new T("cdk-focus-monitor-default-options"),
        jl = Ll({ passive: !0, capture: !0 });
      let XN = (() => {
        class n {
          constructor(t, i, r, s, o) {
            (this._ngZone = t),
              (this._platform = i),
              (this._inputModalityDetector = r),
              (this._origin = null),
              (this._windowFocused = !1),
              (this._originFromTouchInteraction = !1),
              (this._elementInfo = new Map()),
              (this._monitoredElementCount = 0),
              (this._rootNodeFocusListenerCount = new Map()),
              (this._windowFocusListener = () => {
                (this._windowFocused = !0),
                  (this._windowFocusTimeoutId = window.setTimeout(
                    () => (this._windowFocused = !1)
                  ));
              }),
              (this._stopInputModalityDetector = new le()),
              (this._rootNodeFocusAndBlurListener = (a) => {
                const l = Yi(a),
                  c = "focus" === a.type ? this._onFocus : this._onBlur;
                for (let u = l; u; u = u.parentElement) c.call(this, a, u);
              }),
              (this._document = s),
              (this._detectionMode =
                (null == o ? void 0 : o.detectionMode) || 0);
          }
          monitor(t, i = !1) {
            const r = ei(t);
            if (!this._platform.isBrowser || 1 !== r.nodeType) return H(null);
            const s =
                (function vN(n) {
                  if (
                    (function yN() {
                      if (null == tf) {
                        const n =
                          "undefined" != typeof document ? document.head : null;
                        tf = !(!n || (!n.createShadowRoot && !n.attachShadow));
                      }
                      return tf;
                    })()
                  ) {
                    const e = n.getRootNode ? n.getRootNode() : null;
                    if (
                      "undefined" != typeof ShadowRoot &&
                      ShadowRoot &&
                      e instanceof ShadowRoot
                    )
                      return e;
                  }
                  return null;
                })(r) || this._getDocument(),
              o = this._elementInfo.get(r);
            if (o) return i && (o.checkChildren = !0), o.subject;
            const a = { checkChildren: i, subject: new le(), rootNode: s };
            return (
              this._elementInfo.set(r, a),
              this._registerGlobalListeners(a),
              a.subject
            );
          }
          stopMonitoring(t) {
            const i = ei(t),
              r = this._elementInfo.get(i);
            r &&
              (r.subject.complete(),
              this._setClasses(i),
              this._elementInfo.delete(i),
              this._removeGlobalListeners(r));
          }
          focusVia(t, i, r) {
            const s = ei(t);
            s === this._getDocument().activeElement
              ? this._getClosestElementsInfo(s).forEach(([a, l]) =>
                  this._originChanged(a, i, l)
                )
              : (this._setOrigin(i),
                "function" == typeof s.focus && s.focus(r));
          }
          ngOnDestroy() {
            this._elementInfo.forEach((t, i) => this.stopMonitoring(i));
          }
          _getDocument() {
            return this._document || document;
          }
          _getWindow() {
            return this._getDocument().defaultView || window;
          }
          _getFocusOrigin(t) {
            return this._origin
              ? this._originFromTouchInteraction
                ? this._shouldBeAttributedToTouch(t)
                  ? "touch"
                  : "program"
                : this._origin
              : this._windowFocused && this._lastFocusOrigin
              ? this._lastFocusOrigin
              : "program";
          }
          _shouldBeAttributedToTouch(t) {
            return (
              1 === this._detectionMode ||
              !!(null == t
                ? void 0
                : t.contains(this._inputModalityDetector._mostRecentTarget))
            );
          }
          _setClasses(t, i) {
            t.classList.toggle("cdk-focused", !!i),
              t.classList.toggle("cdk-touch-focused", "touch" === i),
              t.classList.toggle("cdk-keyboard-focused", "keyboard" === i),
              t.classList.toggle("cdk-mouse-focused", "mouse" === i),
              t.classList.toggle("cdk-program-focused", "program" === i);
          }
          _setOrigin(t, i = !1) {
            this._ngZone.runOutsideAngular(() => {
              (this._origin = t),
                (this._originFromTouchInteraction = "touch" === t && i),
                0 === this._detectionMode &&
                  (clearTimeout(this._originTimeoutId),
                  (this._originTimeoutId = setTimeout(
                    () => (this._origin = null),
                    this._originFromTouchInteraction ? 650 : 1
                  )));
            });
          }
          _onFocus(t, i) {
            const r = this._elementInfo.get(i),
              s = Yi(t);
            !r ||
              (!r.checkChildren && i !== s) ||
              this._originChanged(i, this._getFocusOrigin(s), r);
          }
          _onBlur(t, i) {
            const r = this._elementInfo.get(i);
            !r ||
              (r.checkChildren &&
                t.relatedTarget instanceof Node &&
                i.contains(t.relatedTarget)) ||
              (this._setClasses(i), this._emitOrigin(r.subject, null));
          }
          _emitOrigin(t, i) {
            this._ngZone.run(() => t.next(i));
          }
          _registerGlobalListeners(t) {
            if (!this._platform.isBrowser) return;
            const i = t.rootNode,
              r = this._rootNodeFocusListenerCount.get(i) || 0;
            r ||
              this._ngZone.runOutsideAngular(() => {
                i.addEventListener(
                  "focus",
                  this._rootNodeFocusAndBlurListener,
                  jl
                ),
                  i.addEventListener(
                    "blur",
                    this._rootNodeFocusAndBlurListener,
                    jl
                  );
              }),
              this._rootNodeFocusListenerCount.set(i, r + 1),
              1 == ++this._monitoredElementCount &&
                (this._ngZone.runOutsideAngular(() => {
                  this._getWindow().addEventListener(
                    "focus",
                    this._windowFocusListener
                  );
                }),
                this._inputModalityDetector.modalityDetected
                  .pipe(Nt(this._stopInputModalityDetector))
                  .subscribe((s) => {
                    this._setOrigin(s, !0);
                  }));
          }
          _removeGlobalListeners(t) {
            const i = t.rootNode;
            if (this._rootNodeFocusListenerCount.has(i)) {
              const r = this._rootNodeFocusListenerCount.get(i);
              r > 1
                ? this._rootNodeFocusListenerCount.set(i, r - 1)
                : (i.removeEventListener(
                    "focus",
                    this._rootNodeFocusAndBlurListener,
                    jl
                  ),
                  i.removeEventListener(
                    "blur",
                    this._rootNodeFocusAndBlurListener,
                    jl
                  ),
                  this._rootNodeFocusListenerCount.delete(i));
            }
            --this._monitoredElementCount ||
              (this._getWindow().removeEventListener(
                "focus",
                this._windowFocusListener
              ),
              this._stopInputModalityDetector.next(),
              clearTimeout(this._windowFocusTimeoutId),
              clearTimeout(this._originTimeoutId));
          }
          _originChanged(t, i, r) {
            this._setClasses(t, i),
              this._emitOrigin(r.subject, i),
              (this._lastFocusOrigin = i);
          }
          _getClosestElementsInfo(t) {
            const i = [];
            return (
              this._elementInfo.forEach((r, s) => {
                (s === t || (r.checkChildren && s.contains(t))) &&
                  i.push([s, r]);
              }),
              i
            );
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(ee), b(Jt), b(qN), b(ue, 8), b(QN, 8));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
          n
        );
      })();
      const Uw = "cdk-high-contrast-black-on-white",
        $w = "cdk-high-contrast-white-on-black",
        df = "cdk-high-contrast-active";
      let JN = (() => {
        class n {
          constructor(t, i) {
            (this._platform = t), (this._document = i);
          }
          getHighContrastMode() {
            if (!this._platform.isBrowser) return 0;
            const t = this._document.createElement("div");
            (t.style.backgroundColor = "rgb(1,2,3)"),
              (t.style.position = "absolute"),
              this._document.body.appendChild(t);
            const i = this._document.defaultView || window,
              r = i && i.getComputedStyle ? i.getComputedStyle(t) : null,
              s = ((r && r.backgroundColor) || "").replace(/ /g, "");
            switch ((t.remove(), s)) {
              case "rgb(0,0,0)":
                return 2;
              case "rgb(255,255,255)":
                return 1;
            }
            return 0;
          }
          _applyBodyHighContrastModeCssClasses() {
            if (
              !this._hasCheckedHighContrastMode &&
              this._platform.isBrowser &&
              this._document.body
            ) {
              const t = this._document.body.classList;
              t.remove(df),
                t.remove(Uw),
                t.remove($w),
                (this._hasCheckedHighContrastMode = !0);
              const i = this.getHighContrastMode();
              1 === i
                ? (t.add(df), t.add(Uw))
                : 2 === i && (t.add(df), t.add($w));
            }
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(Jt), b(ue));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
          n
        );
      })();
      class zw {}
      const ti = "*";
      function hf(n, e) {
        return { type: 7, name: n, definitions: e, options: {} };
      }
      function ff(n, e = null) {
        return { type: 4, styles: e, timings: n };
      }
      function Gw(n, e = null) {
        return { type: 2, steps: n, options: e };
      }
      function Di(n) {
        return { type: 6, styles: n, offset: null };
      }
      function Hl(n, e, t) {
        return { type: 0, name: n, styles: e, options: t };
      }
      function Ul(n, e, t = null) {
        return { type: 1, expr: n, animation: e, options: t };
      }
      function tL(n = null) {
        return { type: 9, options: n };
      }
      function nL(n, e, t = null) {
        return { type: 11, selector: n, animation: e, options: t };
      }
      function qw(n) {
        Promise.resolve(null).then(n);
      }
      class as {
        constructor(e = 0, t = 0) {
          (this._onDoneFns = []),
            (this._onStartFns = []),
            (this._onDestroyFns = []),
            (this._started = !1),
            (this._destroyed = !1),
            (this._finished = !1),
            (this._position = 0),
            (this.parentPlayer = null),
            (this.totalTime = e + t);
        }
        _onFinish() {
          this._finished ||
            ((this._finished = !0),
            this._onDoneFns.forEach((e) => e()),
            (this._onDoneFns = []));
        }
        onStart(e) {
          this._onStartFns.push(e);
        }
        onDone(e) {
          this._onDoneFns.push(e);
        }
        onDestroy(e) {
          this._onDestroyFns.push(e);
        }
        hasStarted() {
          return this._started;
        }
        init() {}
        play() {
          this.hasStarted() || (this._onStart(), this.triggerMicrotask()),
            (this._started = !0);
        }
        triggerMicrotask() {
          qw(() => this._onFinish());
        }
        _onStart() {
          this._onStartFns.forEach((e) => e()), (this._onStartFns = []);
        }
        pause() {}
        restart() {}
        finish() {
          this._onFinish();
        }
        destroy() {
          this._destroyed ||
            ((this._destroyed = !0),
            this.hasStarted() || this._onStart(),
            this.finish(),
            this._onDestroyFns.forEach((e) => e()),
            (this._onDestroyFns = []));
        }
        reset() {
          this._started = !1;
        }
        setPosition(e) {
          this._position = this.totalTime ? e * this.totalTime : 1;
        }
        getPosition() {
          return this.totalTime ? this._position / this.totalTime : 1;
        }
        triggerCallback(e) {
          const t = "start" == e ? this._onStartFns : this._onDoneFns;
          t.forEach((i) => i()), (t.length = 0);
        }
      }
      class Ww {
        constructor(e) {
          (this._onDoneFns = []),
            (this._onStartFns = []),
            (this._finished = !1),
            (this._started = !1),
            (this._destroyed = !1),
            (this._onDestroyFns = []),
            (this.parentPlayer = null),
            (this.totalTime = 0),
            (this.players = e);
          let t = 0,
            i = 0,
            r = 0;
          const s = this.players.length;
          0 == s
            ? qw(() => this._onFinish())
            : this.players.forEach((o) => {
                o.onDone(() => {
                  ++t == s && this._onFinish();
                }),
                  o.onDestroy(() => {
                    ++i == s && this._onDestroy();
                  }),
                  o.onStart(() => {
                    ++r == s && this._onStart();
                  });
              }),
            (this.totalTime = this.players.reduce(
              (o, a) => Math.max(o, a.totalTime),
              0
            ));
        }
        _onFinish() {
          this._finished ||
            ((this._finished = !0),
            this._onDoneFns.forEach((e) => e()),
            (this._onDoneFns = []));
        }
        init() {
          this.players.forEach((e) => e.init());
        }
        onStart(e) {
          this._onStartFns.push(e);
        }
        _onStart() {
          this.hasStarted() ||
            ((this._started = !0),
            this._onStartFns.forEach((e) => e()),
            (this._onStartFns = []));
        }
        onDone(e) {
          this._onDoneFns.push(e);
        }
        onDestroy(e) {
          this._onDestroyFns.push(e);
        }
        hasStarted() {
          return this._started;
        }
        play() {
          this.parentPlayer || this.init(),
            this._onStart(),
            this.players.forEach((e) => e.play());
        }
        pause() {
          this.players.forEach((e) => e.pause());
        }
        restart() {
          this.players.forEach((e) => e.restart());
        }
        finish() {
          this._onFinish(), this.players.forEach((e) => e.finish());
        }
        destroy() {
          this._onDestroy();
        }
        _onDestroy() {
          this._destroyed ||
            ((this._destroyed = !0),
            this._onFinish(),
            this.players.forEach((e) => e.destroy()),
            this._onDestroyFns.forEach((e) => e()),
            (this._onDestroyFns = []));
        }
        reset() {
          this.players.forEach((e) => e.reset()),
            (this._destroyed = !1),
            (this._finished = !1),
            (this._started = !1);
        }
        setPosition(e) {
          const t = e * this.totalTime;
          this.players.forEach((i) => {
            const r = i.totalTime ? Math.min(1, t / i.totalTime) : 1;
            i.setPosition(r);
          });
        }
        getPosition() {
          const e = this.players.reduce(
            (t, i) => (null === t || i.totalTime > t.totalTime ? i : t),
            null
          );
          return null != e ? e.getPosition() : 0;
        }
        beforeDestroy() {
          this.players.forEach((e) => {
            e.beforeDestroy && e.beforeDestroy();
          });
        }
        triggerCallback(e) {
          const t = "start" == e ? this._onStartFns : this._onDoneFns;
          t.forEach((i) => i()), (t.length = 0);
        }
      }
      function Kw() {
        return "undefined" != typeof window && void 0 !== window.document;
      }
      function gf() {
        return (
          "undefined" != typeof process &&
          "[object process]" === {}.toString.call(process)
        );
      }
      function Ei(n) {
        switch (n.length) {
          case 0:
            return new as();
          case 1:
            return n[0];
          default:
            return new Ww(n);
        }
      }
      function Yw(n, e, t, i, r = {}, s = {}) {
        const o = [],
          a = [];
        let l = -1,
          c = null;
        if (
          (i.forEach((u) => {
            const d = u.offset,
              h = d == l,
              f = (h && c) || {};
            Object.keys(u).forEach((p) => {
              let g = p,
                y = u[p];
              if ("offset" !== p)
                switch (((g = e.normalizePropertyName(g, o)), y)) {
                  case "!":
                    y = r[p];
                    break;
                  case ti:
                    y = s[p];
                    break;
                  default:
                    y = e.normalizeStyleValue(p, g, y, o);
                }
              f[g] = y;
            }),
              h || a.push(f),
              (c = f),
              (l = d);
          }),
          o.length)
        ) {
          const u = "\n - ";
          throw new Error(
            `Unable to animate due to the following errors:${u}${o.join(u)}`
          );
        }
        return a;
      }
      function mf(n, e, t, i) {
        switch (e) {
          case "start":
            n.onStart(() => i(t && _f(t, "start", n)));
            break;
          case "done":
            n.onDone(() => i(t && _f(t, "done", n)));
            break;
          case "destroy":
            n.onDestroy(() => i(t && _f(t, "destroy", n)));
        }
      }
      function _f(n, e, t) {
        const i = t.totalTime,
          s = yf(
            n.element,
            n.triggerName,
            n.fromState,
            n.toState,
            e || n.phaseName,
            null == i ? n.totalTime : i,
            !!t.disabled
          ),
          o = n._data;
        return null != o && (s._data = o), s;
      }
      function yf(n, e, t, i, r = "", s = 0, o) {
        return {
          element: n,
          triggerName: e,
          fromState: t,
          toState: i,
          phaseName: r,
          totalTime: s,
          disabled: !!o,
        };
      }
      function Lt(n, e, t) {
        let i;
        return (
          n instanceof Map
            ? ((i = n.get(e)), i || n.set(e, (i = t)))
            : ((i = n[e]), i || (i = n[e] = t)),
          i
        );
      }
      function Zw(n) {
        const e = n.indexOf(":");
        return [n.substring(1, e), n.substr(e + 1)];
      }
      let vf = (n, e) => !1,
        Qw = (n, e, t) => [];
      (gf() || "undefined" != typeof Element) &&
        ((vf = Kw()
          ? (n, e) => {
              for (; e && e !== document.documentElement; ) {
                if (e === n) return !0;
                e = e.parentNode || e.host;
              }
              return !1;
            }
          : (n, e) => n.contains(e)),
        (Qw = (n, e, t) => {
          if (t) return Array.from(n.querySelectorAll(e));
          const i = n.querySelector(e);
          return i ? [i] : [];
        }));
      let Zi = null,
        Xw = !1;
      function bf(n) {
        Zi ||
          ((Zi =
            (function rL() {
              return "undefined" != typeof document ? document.body : null;
            })() || {}),
          (Xw = !!Zi.style && "WebkitAppearance" in Zi.style));
        let e = !0;
        return (
          Zi.style &&
            !(function iL(n) {
              return "ebkit" == n.substring(1, 6);
            })(n) &&
            ((e = n in Zi.style),
            !e &&
              Xw &&
              (e =
                "Webkit" + n.charAt(0).toUpperCase() + n.substr(1) in
                Zi.style)),
          e
        );
      }
      const Cf = vf,
        wf = Qw;
      function Jw(n) {
        const e = {};
        return (
          Object.keys(n).forEach((t) => {
            const i = t.replace(/([a-z])([A-Z])/g, "$1-$2");
            e[i] = n[t];
          }),
          e
        );
      }
      let eD = (() => {
          class n {
            validateStyleProperty(t) {
              return bf(t);
            }
            matchesElement(t, i) {
              return !1;
            }
            containsElement(t, i) {
              return Cf(t, i);
            }
            query(t, i, r) {
              return wf(t, i, r);
            }
            computeStyle(t, i, r) {
              return r || "";
            }
            animate(t, i, r, s, o, a = [], l) {
              return new as(r, s);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })(),
        Df = (() => {
          class n {}
          return (n.NOOP = new eD()), n;
        })();
      const Ef = "ng-enter",
        $l = "ng-leave",
        zl = "ng-trigger",
        Gl = ".ng-trigger",
        nD = "ng-animating",
        Mf = ".ng-animating";
      function Qi(n) {
        if ("number" == typeof n) return n;
        const e = n.match(/^(-?[\.\d]+)(m?s)/);
        return !e || e.length < 2 ? 0 : Sf(parseFloat(e[1]), e[2]);
      }
      function Sf(n, e) {
        return "s" === e ? 1e3 * n : n;
      }
      function ql(n, e, t) {
        return n.hasOwnProperty("duration")
          ? n
          : (function aL(n, e, t) {
              let r,
                s = 0,
                o = "";
              if ("string" == typeof n) {
                const a = n.match(
                  /^(-?[\.\d]+)(m?s)(?:\s+(-?[\.\d]+)(m?s))?(?:\s+([-a-z]+(?:\(.+?\))?))?$/i
                );
                if (null === a)
                  return (
                    e.push(`The provided timing value "${n}" is invalid.`),
                    { duration: 0, delay: 0, easing: "" }
                  );
                r = Sf(parseFloat(a[1]), a[2]);
                const l = a[3];
                null != l && (s = Sf(parseFloat(l), a[4]));
                const c = a[5];
                c && (o = c);
              } else r = n;
              if (!t) {
                let a = !1,
                  l = e.length;
                r < 0 &&
                  (e.push(
                    "Duration values below 0 are not allowed for this animation step."
                  ),
                  (a = !0)),
                  s < 0 &&
                    (e.push(
                      "Delay values below 0 are not allowed for this animation step."
                    ),
                    (a = !0)),
                  a &&
                    e.splice(
                      l,
                      0,
                      `The provided timing value "${n}" is invalid.`
                    );
              }
              return { duration: r, delay: s, easing: o };
            })(n, e, t);
      }
      function ls(n, e = {}) {
        return (
          Object.keys(n).forEach((t) => {
            e[t] = n[t];
          }),
          e
        );
      }
      function Mi(n, e, t = {}) {
        if (e) for (let i in n) t[i] = n[i];
        else ls(n, t);
        return t;
      }
      function rD(n, e, t) {
        return t ? e + ":" + t + ";" : "";
      }
      function sD(n) {
        let e = "";
        for (let t = 0; t < n.style.length; t++) {
          const i = n.style.item(t);
          e += rD(0, i, n.style.getPropertyValue(i));
        }
        for (const t in n.style)
          n.style.hasOwnProperty(t) &&
            !t.startsWith("_") &&
            (e += rD(0, uL(t), n.style[t]));
        n.setAttribute("style", e);
      }
      function Ln(n, e, t) {
        n.style &&
          (Object.keys(e).forEach((i) => {
            const r = Tf(i);
            t && !t.hasOwnProperty(i) && (t[i] = n.style[r]),
              (n.style[r] = e[i]);
          }),
          gf() && sD(n));
      }
      function Xi(n, e) {
        n.style &&
          (Object.keys(e).forEach((t) => {
            const i = Tf(t);
            n.style[i] = "";
          }),
          gf() && sD(n));
      }
      function Ro(n) {
        return Array.isArray(n) ? (1 == n.length ? n[0] : Gw(n)) : n;
      }
      const Af = new RegExp("{{\\s*(.+?)\\s*}}", "g");
      function oD(n) {
        let e = [];
        if ("string" == typeof n) {
          let t;
          for (; (t = Af.exec(n)); ) e.push(t[1]);
          Af.lastIndex = 0;
        }
        return e;
      }
      function Wl(n, e, t) {
        const i = n.toString(),
          r = i.replace(Af, (s, o) => {
            let a = e[o];
            return (
              e.hasOwnProperty(o) ||
                (t.push(`Please provide a value for the animation param ${o}`),
                (a = "")),
              a.toString()
            );
          });
        return r == i ? n : r;
      }
      function Kl(n) {
        const e = [];
        let t = n.next();
        for (; !t.done; ) e.push(t.value), (t = n.next());
        return e;
      }
      const cL = /-+([a-z0-9])/g;
      function Tf(n) {
        return n.replace(cL, (...e) => e[1].toUpperCase());
      }
      function uL(n) {
        return n.replace(/([a-z])([A-Z])/g, "$1-$2").toLowerCase();
      }
      function aD(n, e) {
        return 0 === n || 0 === e;
      }
      function lD(n, e, t) {
        const i = Object.keys(t);
        if (i.length && e.length) {
          let s = e[0],
            o = [];
          if (
            (i.forEach((a) => {
              s.hasOwnProperty(a) || o.push(a), (s[a] = t[a]);
            }),
            o.length)
          )
            for (var r = 1; r < e.length; r++) {
              let a = e[r];
              o.forEach(function (l) {
                a[l] = Of(n, l);
              });
            }
        }
        return e;
      }
      function Vt(n, e, t) {
        switch (e.type) {
          case 7:
            return n.visitTrigger(e, t);
          case 0:
            return n.visitState(e, t);
          case 1:
            return n.visitTransition(e, t);
          case 2:
            return n.visitSequence(e, t);
          case 3:
            return n.visitGroup(e, t);
          case 4:
            return n.visitAnimate(e, t);
          case 5:
            return n.visitKeyframes(e, t);
          case 6:
            return n.visitStyle(e, t);
          case 8:
            return n.visitReference(e, t);
          case 9:
            return n.visitAnimateChild(e, t);
          case 10:
            return n.visitAnimateRef(e, t);
          case 11:
            return n.visitQuery(e, t);
          case 12:
            return n.visitStagger(e, t);
          default:
            throw new Error(
              `Unable to resolve animation metadata node #${e.type}`
            );
        }
      }
      function Of(n, e) {
        return window.getComputedStyle(n)[e];
      }
      function dL(n, e) {
        const t = [];
        return (
          "string" == typeof n
            ? n.split(/\s*,\s*/).forEach((i) =>
                (function hL(n, e, t) {
                  if (":" == n[0]) {
                    const l = (function fL(n, e) {
                      switch (n) {
                        case ":enter":
                          return "void => *";
                        case ":leave":
                          return "* => void";
                        case ":increment":
                          return (t, i) => parseFloat(i) > parseFloat(t);
                        case ":decrement":
                          return (t, i) => parseFloat(i) < parseFloat(t);
                        default:
                          return (
                            e.push(
                              `The transition alias value "${n}" is not supported`
                            ),
                            "* => *"
                          );
                      }
                    })(n, t);
                    if ("function" == typeof l) return void e.push(l);
                    n = l;
                  }
                  const i = n.match(/^(\*|[-\w]+)\s*(<?[=-]>)\s*(\*|[-\w]+)$/);
                  if (null == i || i.length < 4)
                    return (
                      t.push(
                        `The provided transition expression "${n}" is not supported`
                      ),
                      e
                    );
                  const r = i[1],
                    s = i[2],
                    o = i[3];
                  e.push(cD(r, o));
                  "<" == s[0] && !("*" == r && "*" == o) && e.push(cD(o, r));
                })(i, t, e)
              )
            : t.push(n),
          t
        );
      }
      const Zl = new Set(["true", "1"]),
        Ql = new Set(["false", "0"]);
      function cD(n, e) {
        const t = Zl.has(n) || Ql.has(n),
          i = Zl.has(e) || Ql.has(e);
        return (r, s) => {
          let o = "*" == n || n == r,
            a = "*" == e || e == s;
          return (
            !o && t && "boolean" == typeof r && (o = r ? Zl.has(n) : Ql.has(n)),
            !a && i && "boolean" == typeof s && (a = s ? Zl.has(e) : Ql.has(e)),
            o && a
          );
        };
      }
      const pL = new RegExp("s*:selfs*,?", "g");
      function If(n, e, t) {
        return new gL(n).build(e, t);
      }
      class gL {
        constructor(e) {
          this._driver = e;
        }
        build(e, t) {
          const i = new yL(t);
          return this._resetContextStyleTimingState(i), Vt(this, Ro(e), i);
        }
        _resetContextStyleTimingState(e) {
          (e.currentQuerySelector = ""),
            (e.collectedStyles = {}),
            (e.collectedStyles[""] = {}),
            (e.currentTime = 0);
        }
        visitTrigger(e, t) {
          let i = (t.queryCount = 0),
            r = (t.depCount = 0);
          const s = [],
            o = [];
          return (
            "@" == e.name.charAt(0) &&
              t.errors.push(
                "animation triggers cannot be prefixed with an `@` sign (e.g. trigger('@foo', [...]))"
              ),
            e.definitions.forEach((a) => {
              if ((this._resetContextStyleTimingState(t), 0 == a.type)) {
                const l = a,
                  c = l.name;
                c
                  .toString()
                  .split(/\s*,\s*/)
                  .forEach((u) => {
                    (l.name = u), s.push(this.visitState(l, t));
                  }),
                  (l.name = c);
              } else if (1 == a.type) {
                const l = this.visitTransition(a, t);
                (i += l.queryCount), (r += l.depCount), o.push(l);
              } else
                t.errors.push(
                  "only state() and transition() definitions can sit inside of a trigger()"
                );
            }),
            {
              type: 7,
              name: e.name,
              states: s,
              transitions: o,
              queryCount: i,
              depCount: r,
              options: null,
            }
          );
        }
        visitState(e, t) {
          const i = this.visitStyle(e.styles, t),
            r = (e.options && e.options.params) || null;
          if (i.containsDynamicStyles) {
            const s = new Set(),
              o = r || {};
            if (
              (i.styles.forEach((a) => {
                if (Xl(a)) {
                  const l = a;
                  Object.keys(l).forEach((c) => {
                    oD(l[c]).forEach((u) => {
                      o.hasOwnProperty(u) || s.add(u);
                    });
                  });
                }
              }),
              s.size)
            ) {
              const a = Kl(s.values());
              t.errors.push(
                `state("${
                  e.name
                }", ...) must define default values for all the following style substitutions: ${a.join(
                  ", "
                )}`
              );
            }
          }
          return {
            type: 0,
            name: e.name,
            style: i,
            options: r ? { params: r } : null,
          };
        }
        visitTransition(e, t) {
          (t.queryCount = 0), (t.depCount = 0);
          const i = Vt(this, Ro(e.animation), t);
          return {
            type: 1,
            matchers: dL(e.expr, t.errors),
            animation: i,
            queryCount: t.queryCount,
            depCount: t.depCount,
            options: Ji(e.options),
          };
        }
        visitSequence(e, t) {
          return {
            type: 2,
            steps: e.steps.map((i) => Vt(this, i, t)),
            options: Ji(e.options),
          };
        }
        visitGroup(e, t) {
          const i = t.currentTime;
          let r = 0;
          const s = e.steps.map((o) => {
            t.currentTime = i;
            const a = Vt(this, o, t);
            return (r = Math.max(r, t.currentTime)), a;
          });
          return (
            (t.currentTime = r), { type: 3, steps: s, options: Ji(e.options) }
          );
        }
        visitAnimate(e, t) {
          const i = (function bL(n, e) {
            let t = null;
            if (n.hasOwnProperty("duration")) t = n;
            else if ("number" == typeof n) return xf(ql(n, e).duration, 0, "");
            const i = n;
            if (
              i
                .split(/\s+/)
                .some((s) => "{" == s.charAt(0) && "{" == s.charAt(1))
            ) {
              const s = xf(0, 0, "");
              return (s.dynamic = !0), (s.strValue = i), s;
            }
            return (t = t || ql(i, e)), xf(t.duration, t.delay, t.easing);
          })(e.timings, t.errors);
          t.currentAnimateTimings = i;
          let r,
            s = e.styles ? e.styles : Di({});
          if (5 == s.type) r = this.visitKeyframes(s, t);
          else {
            let o = e.styles,
              a = !1;
            if (!o) {
              a = !0;
              const c = {};
              i.easing && (c.easing = i.easing), (o = Di(c));
            }
            t.currentTime += i.duration + i.delay;
            const l = this.visitStyle(o, t);
            (l.isEmptyStep = a), (r = l);
          }
          return (
            (t.currentAnimateTimings = null),
            { type: 4, timings: i, style: r, options: null }
          );
        }
        visitStyle(e, t) {
          const i = this._makeStyleAst(e, t);
          return this._validateStyleAst(i, t), i;
        }
        _makeStyleAst(e, t) {
          const i = [];
          Array.isArray(e.styles)
            ? e.styles.forEach((o) => {
                "string" == typeof o
                  ? o == ti
                    ? i.push(o)
                    : t.errors.push(
                        `The provided style string value ${o} is not allowed.`
                      )
                  : i.push(o);
              })
            : i.push(e.styles);
          let r = !1,
            s = null;
          return (
            i.forEach((o) => {
              if (Xl(o)) {
                const a = o,
                  l = a.easing;
                if ((l && ((s = l), delete a.easing), !r))
                  for (let c in a)
                    if (a[c].toString().indexOf("{{") >= 0) {
                      r = !0;
                      break;
                    }
              }
            }),
            {
              type: 6,
              styles: i,
              easing: s,
              offset: e.offset,
              containsDynamicStyles: r,
              options: null,
            }
          );
        }
        _validateStyleAst(e, t) {
          const i = t.currentAnimateTimings;
          let r = t.currentTime,
            s = t.currentTime;
          i && s > 0 && (s -= i.duration + i.delay),
            e.styles.forEach((o) => {
              "string" != typeof o &&
                Object.keys(o).forEach((a) => {
                  if (!this._driver.validateStyleProperty(a))
                    return void t.errors.push(
                      `The provided animation property "${a}" is not a supported CSS property for animations`
                    );
                  const l = t.collectedStyles[t.currentQuerySelector],
                    c = l[a];
                  let u = !0;
                  c &&
                    (s != r &&
                      s >= c.startTime &&
                      r <= c.endTime &&
                      (t.errors.push(
                        `The CSS property "${a}" that exists between the times of "${c.startTime}ms" and "${c.endTime}ms" is also being animated in a parallel animation between the times of "${s}ms" and "${r}ms"`
                      ),
                      (u = !1)),
                    (s = c.startTime)),
                    u && (l[a] = { startTime: s, endTime: r }),
                    t.options &&
                      (function lL(n, e, t) {
                        const i = e.params || {},
                          r = oD(n);
                        r.length &&
                          r.forEach((s) => {
                            i.hasOwnProperty(s) ||
                              t.push(
                                `Unable to resolve the local animation param ${s} in the given list of values`
                              );
                          });
                      })(o[a], t.options, t.errors);
                });
            });
        }
        visitKeyframes(e, t) {
          const i = { type: 5, styles: [], options: null };
          if (!t.currentAnimateTimings)
            return (
              t.errors.push(
                "keyframes() must be placed inside of a call to animate()"
              ),
              i
            );
          let s = 0;
          const o = [];
          let a = !1,
            l = !1,
            c = 0;
          const u = e.steps.map((v) => {
            const m = this._makeStyleAst(v, t);
            let w =
                null != m.offset
                  ? m.offset
                  : (function vL(n) {
                      if ("string" == typeof n) return null;
                      let e = null;
                      if (Array.isArray(n))
                        n.forEach((t) => {
                          if (Xl(t) && t.hasOwnProperty("offset")) {
                            const i = t;
                            (e = parseFloat(i.offset)), delete i.offset;
                          }
                        });
                      else if (Xl(n) && n.hasOwnProperty("offset")) {
                        const t = n;
                        (e = parseFloat(t.offset)), delete t.offset;
                      }
                      return e;
                    })(m.styles),
              A = 0;
            return (
              null != w && (s++, (A = m.offset = w)),
              (l = l || A < 0 || A > 1),
              (a = a || A < c),
              (c = A),
              o.push(A),
              m
            );
          });
          l &&
            t.errors.push(
              "Please ensure that all keyframe offsets are between 0 and 1"
            ),
            a &&
              t.errors.push(
                "Please ensure that all keyframe offsets are in order"
              );
          const d = e.steps.length;
          let h = 0;
          s > 0 && s < d
            ? t.errors.push(
                "Not all style() steps within the declared keyframes() contain offsets"
              )
            : 0 == s && (h = 1 / (d - 1));
          const f = d - 1,
            p = t.currentTime,
            g = t.currentAnimateTimings,
            y = g.duration;
          return (
            u.forEach((v, m) => {
              const w = h > 0 ? (m == f ? 1 : h * m) : o[m],
                A = w * y;
              (t.currentTime = p + g.delay + A),
                (g.duration = A),
                this._validateStyleAst(v, t),
                (v.offset = w),
                i.styles.push(v);
            }),
            i
          );
        }
        visitReference(e, t) {
          return {
            type: 8,
            animation: Vt(this, Ro(e.animation), t),
            options: Ji(e.options),
          };
        }
        visitAnimateChild(e, t) {
          return t.depCount++, { type: 9, options: Ji(e.options) };
        }
        visitAnimateRef(e, t) {
          return {
            type: 10,
            animation: this.visitReference(e.animation, t),
            options: Ji(e.options),
          };
        }
        visitQuery(e, t) {
          const i = t.currentQuerySelector,
            r = e.options || {};
          t.queryCount++, (t.currentQuery = e);
          const [s, o] = (function mL(n) {
            const e = !!n.split(/\s*,\s*/).find((t) => ":self" == t);
            return (
              e && (n = n.replace(pL, "")),
              (n = n
                .replace(/@\*/g, Gl)
                .replace(/@\w+/g, (t) => Gl + "-" + t.substr(1))
                .replace(/:animating/g, Mf)),
              [n, e]
            );
          })(e.selector);
          (t.currentQuerySelector = i.length ? i + " " + s : s),
            Lt(t.collectedStyles, t.currentQuerySelector, {});
          const a = Vt(this, Ro(e.animation), t);
          return (
            (t.currentQuery = null),
            (t.currentQuerySelector = i),
            {
              type: 11,
              selector: s,
              limit: r.limit || 0,
              optional: !!r.optional,
              includeSelf: o,
              animation: a,
              originalSelector: e.selector,
              options: Ji(e.options),
            }
          );
        }
        visitStagger(e, t) {
          t.currentQuery ||
            t.errors.push("stagger() can only be used inside of query()");
          const i =
            "full" === e.timings
              ? { duration: 0, delay: 0, easing: "full" }
              : ql(e.timings, t.errors, !0);
          return {
            type: 12,
            animation: Vt(this, Ro(e.animation), t),
            timings: i,
            options: null,
          };
        }
      }
      class yL {
        constructor(e) {
          (this.errors = e),
            (this.queryCount = 0),
            (this.depCount = 0),
            (this.currentTransition = null),
            (this.currentQuery = null),
            (this.currentQuerySelector = null),
            (this.currentAnimateTimings = null),
            (this.currentTime = 0),
            (this.collectedStyles = {}),
            (this.options = null);
        }
      }
      function Xl(n) {
        return !Array.isArray(n) && "object" == typeof n;
      }
      function Ji(n) {
        return (
          n
            ? (n = ls(n)).params &&
              (n.params = (function _L(n) {
                return n ? ls(n) : null;
              })(n.params))
            : (n = {}),
          n
        );
      }
      function xf(n, e, t) {
        return { duration: n, delay: e, easing: t };
      }
      function kf(n, e, t, i, r, s, o = null, a = !1) {
        return {
          type: 1,
          element: n,
          keyframes: e,
          preStyleProps: t,
          postStyleProps: i,
          duration: r,
          delay: s,
          totalTime: r + s,
          easing: o,
          subTimeline: a,
        };
      }
      class Jl {
        constructor() {
          this._map = new Map();
        }
        get(e) {
          return this._map.get(e) || [];
        }
        append(e, t) {
          let i = this._map.get(e);
          i || this._map.set(e, (i = [])), i.push(...t);
        }
        has(e) {
          return this._map.has(e);
        }
        clear() {
          this._map.clear();
        }
      }
      const DL = new RegExp(":enter", "g"),
        ML = new RegExp(":leave", "g");
      function Ff(n, e, t, i, r, s = {}, o = {}, a, l, c = []) {
        return new SL().buildKeyframes(n, e, t, i, r, s, o, a, l, c);
      }
      class SL {
        buildKeyframes(e, t, i, r, s, o, a, l, c, u = []) {
          c = c || new Jl();
          const d = new Rf(e, t, c, r, s, u, []);
          (d.options = l),
            d.currentTimeline.setStyles([o], null, d.errors, l),
            Vt(this, i, d);
          const h = d.timelines.filter((f) => f.containsAnimation());
          if (Object.keys(a).length) {
            let f;
            for (let p = h.length - 1; p >= 0; p--) {
              const g = h[p];
              if (g.element === t) {
                f = g;
                break;
              }
            }
            f &&
              !f.allowOnlyTimelineStyles() &&
              f.setStyles([a], null, d.errors, l);
          }
          return h.length
            ? h.map((f) => f.buildKeyframes())
            : [kf(t, [], [], [], 0, 0, "", !1)];
        }
        visitTrigger(e, t) {}
        visitState(e, t) {}
        visitTransition(e, t) {}
        visitAnimateChild(e, t) {
          const i = t.subInstructions.get(t.element);
          if (i) {
            const r = t.createSubContext(e.options),
              s = t.currentTimeline.currentTime,
              o = this._visitSubInstructions(i, r, r.options);
            s != o && t.transformIntoNewTimeline(o);
          }
          t.previousNode = e;
        }
        visitAnimateRef(e, t) {
          const i = t.createSubContext(e.options);
          i.transformIntoNewTimeline(),
            this.visitReference(e.animation, i),
            t.transformIntoNewTimeline(i.currentTimeline.currentTime),
            (t.previousNode = e);
        }
        _visitSubInstructions(e, t, i) {
          let s = t.currentTimeline.currentTime;
          const o = null != i.duration ? Qi(i.duration) : null,
            a = null != i.delay ? Qi(i.delay) : null;
          return (
            0 !== o &&
              e.forEach((l) => {
                const c = t.appendInstructionToTimeline(l, o, a);
                s = Math.max(s, c.duration + c.delay);
              }),
            s
          );
        }
        visitReference(e, t) {
          t.updateOptions(e.options, !0),
            Vt(this, e.animation, t),
            (t.previousNode = e);
        }
        visitSequence(e, t) {
          const i = t.subContextCount;
          let r = t;
          const s = e.options;
          if (
            s &&
            (s.params || s.delay) &&
            ((r = t.createSubContext(s)),
            r.transformIntoNewTimeline(),
            null != s.delay)
          ) {
            6 == r.previousNode.type &&
              (r.currentTimeline.snapshotCurrentStyles(),
              (r.previousNode = ec));
            const o = Qi(s.delay);
            r.delayNextStep(o);
          }
          e.steps.length &&
            (e.steps.forEach((o) => Vt(this, o, r)),
            r.currentTimeline.applyStylesToKeyframe(),
            r.subContextCount > i && r.transformIntoNewTimeline()),
            (t.previousNode = e);
        }
        visitGroup(e, t) {
          const i = [];
          let r = t.currentTimeline.currentTime;
          const s = e.options && e.options.delay ? Qi(e.options.delay) : 0;
          e.steps.forEach((o) => {
            const a = t.createSubContext(e.options);
            s && a.delayNextStep(s),
              Vt(this, o, a),
              (r = Math.max(r, a.currentTimeline.currentTime)),
              i.push(a.currentTimeline);
          }),
            i.forEach((o) => t.currentTimeline.mergeTimelineCollectedStyles(o)),
            t.transformIntoNewTimeline(r),
            (t.previousNode = e);
        }
        _visitTiming(e, t) {
          if (e.dynamic) {
            const i = e.strValue;
            return ql(t.params ? Wl(i, t.params, t.errors) : i, t.errors);
          }
          return { duration: e.duration, delay: e.delay, easing: e.easing };
        }
        visitAnimate(e, t) {
          const i = (t.currentAnimateTimings = this._visitTiming(e.timings, t)),
            r = t.currentTimeline;
          i.delay && (t.incrementTime(i.delay), r.snapshotCurrentStyles());
          const s = e.style;
          5 == s.type
            ? this.visitKeyframes(s, t)
            : (t.incrementTime(i.duration),
              this.visitStyle(s, t),
              r.applyStylesToKeyframe()),
            (t.currentAnimateTimings = null),
            (t.previousNode = e);
        }
        visitStyle(e, t) {
          const i = t.currentTimeline,
            r = t.currentAnimateTimings;
          !r && i.getCurrentStyleProperties().length && i.forwardFrame();
          const s = (r && r.easing) || e.easing;
          e.isEmptyStep
            ? i.applyEmptyStep(s)
            : i.setStyles(e.styles, s, t.errors, t.options),
            (t.previousNode = e);
        }
        visitKeyframes(e, t) {
          const i = t.currentAnimateTimings,
            r = t.currentTimeline.duration,
            s = i.duration,
            a = t.createSubContext().currentTimeline;
          (a.easing = i.easing),
            e.styles.forEach((l) => {
              a.forwardTime((l.offset || 0) * s),
                a.setStyles(l.styles, l.easing, t.errors, t.options),
                a.applyStylesToKeyframe();
            }),
            t.currentTimeline.mergeTimelineCollectedStyles(a),
            t.transformIntoNewTimeline(r + s),
            (t.previousNode = e);
        }
        visitQuery(e, t) {
          const i = t.currentTimeline.currentTime,
            r = e.options || {},
            s = r.delay ? Qi(r.delay) : 0;
          s &&
            (6 === t.previousNode.type ||
              (0 == i &&
                t.currentTimeline.getCurrentStyleProperties().length)) &&
            (t.currentTimeline.snapshotCurrentStyles(), (t.previousNode = ec));
          let o = i;
          const a = t.invokeQuery(
            e.selector,
            e.originalSelector,
            e.limit,
            e.includeSelf,
            !!r.optional,
            t.errors
          );
          t.currentQueryTotal = a.length;
          let l = null;
          a.forEach((c, u) => {
            t.currentQueryIndex = u;
            const d = t.createSubContext(e.options, c);
            s && d.delayNextStep(s),
              c === t.element && (l = d.currentTimeline),
              Vt(this, e.animation, d),
              d.currentTimeline.applyStylesToKeyframe(),
              (o = Math.max(o, d.currentTimeline.currentTime));
          }),
            (t.currentQueryIndex = 0),
            (t.currentQueryTotal = 0),
            t.transformIntoNewTimeline(o),
            l &&
              (t.currentTimeline.mergeTimelineCollectedStyles(l),
              t.currentTimeline.snapshotCurrentStyles()),
            (t.previousNode = e);
        }
        visitStagger(e, t) {
          const i = t.parentContext,
            r = t.currentTimeline,
            s = e.timings,
            o = Math.abs(s.duration),
            a = o * (t.currentQueryTotal - 1);
          let l = o * t.currentQueryIndex;
          switch (s.duration < 0 ? "reverse" : s.easing) {
            case "reverse":
              l = a - l;
              break;
            case "full":
              l = i.currentStaggerTime;
          }
          const u = t.currentTimeline;
          l && u.delayNextStep(l);
          const d = u.currentTime;
          Vt(this, e.animation, t),
            (t.previousNode = e),
            (i.currentStaggerTime =
              r.currentTime - d + (r.startTime - i.currentTimeline.startTime));
        }
      }
      const ec = {};
      class Rf {
        constructor(e, t, i, r, s, o, a, l) {
          (this._driver = e),
            (this.element = t),
            (this.subInstructions = i),
            (this._enterClassName = r),
            (this._leaveClassName = s),
            (this.errors = o),
            (this.timelines = a),
            (this.parentContext = null),
            (this.currentAnimateTimings = null),
            (this.previousNode = ec),
            (this.subContextCount = 0),
            (this.options = {}),
            (this.currentQueryIndex = 0),
            (this.currentQueryTotal = 0),
            (this.currentStaggerTime = 0),
            (this.currentTimeline = l || new tc(this._driver, t, 0)),
            a.push(this.currentTimeline);
        }
        get params() {
          return this.options.params;
        }
        updateOptions(e, t) {
          if (!e) return;
          const i = e;
          let r = this.options;
          null != i.duration && (r.duration = Qi(i.duration)),
            null != i.delay && (r.delay = Qi(i.delay));
          const s = i.params;
          if (s) {
            let o = r.params;
            o || (o = this.options.params = {}),
              Object.keys(s).forEach((a) => {
                (!t || !o.hasOwnProperty(a)) &&
                  (o[a] = Wl(s[a], o, this.errors));
              });
          }
        }
        _copyOptions() {
          const e = {};
          if (this.options) {
            const t = this.options.params;
            if (t) {
              const i = (e.params = {});
              Object.keys(t).forEach((r) => {
                i[r] = t[r];
              });
            }
          }
          return e;
        }
        createSubContext(e = null, t, i) {
          const r = t || this.element,
            s = new Rf(
              this._driver,
              r,
              this.subInstructions,
              this._enterClassName,
              this._leaveClassName,
              this.errors,
              this.timelines,
              this.currentTimeline.fork(r, i || 0)
            );
          return (
            (s.previousNode = this.previousNode),
            (s.currentAnimateTimings = this.currentAnimateTimings),
            (s.options = this._copyOptions()),
            s.updateOptions(e),
            (s.currentQueryIndex = this.currentQueryIndex),
            (s.currentQueryTotal = this.currentQueryTotal),
            (s.parentContext = this),
            this.subContextCount++,
            s
          );
        }
        transformIntoNewTimeline(e) {
          return (
            (this.previousNode = ec),
            (this.currentTimeline = this.currentTimeline.fork(this.element, e)),
            this.timelines.push(this.currentTimeline),
            this.currentTimeline
          );
        }
        appendInstructionToTimeline(e, t, i) {
          const r = {
              duration: null != t ? t : e.duration,
              delay:
                this.currentTimeline.currentTime +
                (null != i ? i : 0) +
                e.delay,
              easing: "",
            },
            s = new AL(
              this._driver,
              e.element,
              e.keyframes,
              e.preStyleProps,
              e.postStyleProps,
              r,
              e.stretchStartingKeyframe
            );
          return this.timelines.push(s), r;
        }
        incrementTime(e) {
          this.currentTimeline.forwardTime(this.currentTimeline.duration + e);
        }
        delayNextStep(e) {
          e > 0 && this.currentTimeline.delayNextStep(e);
        }
        invokeQuery(e, t, i, r, s, o) {
          let a = [];
          if ((r && a.push(this.element), e.length > 0)) {
            e = (e = e.replace(DL, "." + this._enterClassName)).replace(
              ML,
              "." + this._leaveClassName
            );
            let c = this._driver.query(this.element, e, 1 != i);
            0 !== i &&
              (c = i < 0 ? c.slice(c.length + i, c.length) : c.slice(0, i)),
              a.push(...c);
          }
          return (
            !s &&
              0 == a.length &&
              o.push(
                `\`query("${t}")\` returned zero elements. (Use \`query("${t}", { optional: true })\` if you wish to allow this.)`
              ),
            a
          );
        }
      }
      class tc {
        constructor(e, t, i, r) {
          (this._driver = e),
            (this.element = t),
            (this.startTime = i),
            (this._elementTimelineStylesLookup = r),
            (this.duration = 0),
            (this._previousKeyframe = {}),
            (this._currentKeyframe = {}),
            (this._keyframes = new Map()),
            (this._styleSummary = {}),
            (this._pendingStyles = {}),
            (this._backFill = {}),
            (this._currentEmptyStepKeyframe = null),
            this._elementTimelineStylesLookup ||
              (this._elementTimelineStylesLookup = new Map()),
            (this._localTimelineStyles = Object.create(this._backFill, {})),
            (this._globalTimelineStyles =
              this._elementTimelineStylesLookup.get(t)),
            this._globalTimelineStyles ||
              ((this._globalTimelineStyles = this._localTimelineStyles),
              this._elementTimelineStylesLookup.set(
                t,
                this._localTimelineStyles
              )),
            this._loadKeyframe();
        }
        containsAnimation() {
          switch (this._keyframes.size) {
            case 0:
              return !1;
            case 1:
              return this.getCurrentStyleProperties().length > 0;
            default:
              return !0;
          }
        }
        getCurrentStyleProperties() {
          return Object.keys(this._currentKeyframe);
        }
        get currentTime() {
          return this.startTime + this.duration;
        }
        delayNextStep(e) {
          const t =
            1 == this._keyframes.size &&
            Object.keys(this._pendingStyles).length;
          this.duration || t
            ? (this.forwardTime(this.currentTime + e),
              t && this.snapshotCurrentStyles())
            : (this.startTime += e);
        }
        fork(e, t) {
          return (
            this.applyStylesToKeyframe(),
            new tc(
              this._driver,
              e,
              t || this.currentTime,
              this._elementTimelineStylesLookup
            )
          );
        }
        _loadKeyframe() {
          this._currentKeyframe &&
            (this._previousKeyframe = this._currentKeyframe),
            (this._currentKeyframe = this._keyframes.get(this.duration)),
            this._currentKeyframe ||
              ((this._currentKeyframe = Object.create(this._backFill, {})),
              this._keyframes.set(this.duration, this._currentKeyframe));
        }
        forwardFrame() {
          (this.duration += 1), this._loadKeyframe();
        }
        forwardTime(e) {
          this.applyStylesToKeyframe(),
            (this.duration = e),
            this._loadKeyframe();
        }
        _updateStyle(e, t) {
          (this._localTimelineStyles[e] = t),
            (this._globalTimelineStyles[e] = t),
            (this._styleSummary[e] = { time: this.currentTime, value: t });
        }
        allowOnlyTimelineStyles() {
          return this._currentEmptyStepKeyframe !== this._currentKeyframe;
        }
        applyEmptyStep(e) {
          e && (this._previousKeyframe.easing = e),
            Object.keys(this._globalTimelineStyles).forEach((t) => {
              (this._backFill[t] = this._globalTimelineStyles[t] || ti),
                (this._currentKeyframe[t] = ti);
            }),
            (this._currentEmptyStepKeyframe = this._currentKeyframe);
        }
        setStyles(e, t, i, r) {
          t && (this._previousKeyframe.easing = t);
          const s = (r && r.params) || {},
            o = (function TL(n, e) {
              const t = {};
              let i;
              return (
                n.forEach((r) => {
                  "*" === r
                    ? ((i = i || Object.keys(e)),
                      i.forEach((s) => {
                        t[s] = ti;
                      }))
                    : Mi(r, !1, t);
                }),
                t
              );
            })(e, this._globalTimelineStyles);
          Object.keys(o).forEach((a) => {
            const l = Wl(o[a], s, i);
            (this._pendingStyles[a] = l),
              this._localTimelineStyles.hasOwnProperty(a) ||
                (this._backFill[a] = this._globalTimelineStyles.hasOwnProperty(
                  a
                )
                  ? this._globalTimelineStyles[a]
                  : ti),
              this._updateStyle(a, l);
          });
        }
        applyStylesToKeyframe() {
          const e = this._pendingStyles,
            t = Object.keys(e);
          0 != t.length &&
            ((this._pendingStyles = {}),
            t.forEach((i) => {
              this._currentKeyframe[i] = e[i];
            }),
            Object.keys(this._localTimelineStyles).forEach((i) => {
              this._currentKeyframe.hasOwnProperty(i) ||
                (this._currentKeyframe[i] = this._localTimelineStyles[i]);
            }));
        }
        snapshotCurrentStyles() {
          Object.keys(this._localTimelineStyles).forEach((e) => {
            const t = this._localTimelineStyles[e];
            (this._pendingStyles[e] = t), this._updateStyle(e, t);
          });
        }
        getFinalKeyframe() {
          return this._keyframes.get(this.duration);
        }
        get properties() {
          const e = [];
          for (let t in this._currentKeyframe) e.push(t);
          return e;
        }
        mergeTimelineCollectedStyles(e) {
          Object.keys(e._styleSummary).forEach((t) => {
            const i = this._styleSummary[t],
              r = e._styleSummary[t];
            (!i || r.time > i.time) && this._updateStyle(t, r.value);
          });
        }
        buildKeyframes() {
          this.applyStylesToKeyframe();
          const e = new Set(),
            t = new Set(),
            i = 1 === this._keyframes.size && 0 === this.duration;
          let r = [];
          this._keyframes.forEach((a, l) => {
            const c = Mi(a, !0);
            Object.keys(c).forEach((u) => {
              const d = c[u];
              "!" == d ? e.add(u) : d == ti && t.add(u);
            }),
              i || (c.offset = l / this.duration),
              r.push(c);
          });
          const s = e.size ? Kl(e.values()) : [],
            o = t.size ? Kl(t.values()) : [];
          if (i) {
            const a = r[0],
              l = ls(a);
            (a.offset = 0), (l.offset = 1), (r = [a, l]);
          }
          return kf(
            this.element,
            r,
            s,
            o,
            this.duration,
            this.startTime,
            this.easing,
            !1
          );
        }
      }
      class AL extends tc {
        constructor(e, t, i, r, s, o, a = !1) {
          super(e, t, o.delay),
            (this.keyframes = i),
            (this.preStyleProps = r),
            (this.postStyleProps = s),
            (this._stretchStartingKeyframe = a),
            (this.timings = {
              duration: o.duration,
              delay: o.delay,
              easing: o.easing,
            });
        }
        containsAnimation() {
          return this.keyframes.length > 1;
        }
        buildKeyframes() {
          let e = this.keyframes,
            { delay: t, duration: i, easing: r } = this.timings;
          if (this._stretchStartingKeyframe && t) {
            const s = [],
              o = i + t,
              a = t / o,
              l = Mi(e[0], !1);
            (l.offset = 0), s.push(l);
            const c = Mi(e[0], !1);
            (c.offset = hD(a)), s.push(c);
            const u = e.length - 1;
            for (let d = 1; d <= u; d++) {
              let h = Mi(e[d], !1);
              (h.offset = hD((t + h.offset * i) / o)), s.push(h);
            }
            (i = o), (t = 0), (r = ""), (e = s);
          }
          return kf(
            this.element,
            e,
            this.preStyleProps,
            this.postStyleProps,
            i,
            t,
            r,
            !0
          );
        }
      }
      function hD(n, e = 3) {
        const t = Math.pow(10, e - 1);
        return Math.round(n * t) / t;
      }
      class Pf {}
      class OL extends Pf {
        normalizePropertyName(e, t) {
          return Tf(e);
        }
        normalizeStyleValue(e, t, i, r) {
          let s = "";
          const o = i.toString().trim();
          if (IL[t] && 0 !== i && "0" !== i)
            if ("number" == typeof i) s = "px";
            else {
              const a = i.match(/^[+-]?[\d\.]+([a-z]*)$/);
              a &&
                0 == a[1].length &&
                r.push(`Please provide a CSS unit value for ${e}:${i}`);
            }
          return o + s;
        }
      }
      const IL = (() =>
        (function xL(n) {
          const e = {};
          return n.forEach((t) => (e[t] = !0)), e;
        })(
          "width,height,minWidth,minHeight,maxWidth,maxHeight,left,top,bottom,right,fontSize,outlineWidth,outlineOffset,paddingTop,paddingLeft,paddingBottom,paddingRight,marginTop,marginLeft,marginBottom,marginRight,borderRadius,borderWidth,borderTopWidth,borderLeftWidth,borderRightWidth,borderBottomWidth,textIndent,perspective".split(
            ","
          )
        ))();
      function fD(n, e, t, i, r, s, o, a, l, c, u, d, h) {
        return {
          type: 0,
          element: n,
          triggerName: e,
          isRemovalTransition: r,
          fromState: t,
          fromStyles: s,
          toState: i,
          toStyles: o,
          timelines: a,
          queriedElements: l,
          preStyleProps: c,
          postStyleProps: u,
          totalTime: d,
          errors: h,
        };
      }
      const Nf = {};
      class pD {
        constructor(e, t, i) {
          (this._triggerName = e), (this.ast = t), (this._stateStyles = i);
        }
        match(e, t, i, r) {
          return (function kL(n, e, t, i, r) {
            return n.some((s) => s(e, t, i, r));
          })(this.ast.matchers, e, t, i, r);
        }
        buildStyles(e, t, i) {
          const r = this._stateStyles["*"],
            s = this._stateStyles[e],
            o = r ? r.buildStyles(t, i) : {};
          return s ? s.buildStyles(t, i) : o;
        }
        build(e, t, i, r, s, o, a, l, c, u) {
          const d = [],
            h = (this.ast.options && this.ast.options.params) || Nf,
            p = this.buildStyles(i, (a && a.params) || Nf, d),
            g = (l && l.params) || Nf,
            y = this.buildStyles(r, g, d),
            v = new Set(),
            m = new Map(),
            w = new Map(),
            A = "void" === r,
            $ = { params: Object.assign(Object.assign({}, h), g) },
            Ae = u ? [] : Ff(e, t, this.ast.animation, s, o, p, y, $, c, d);
          let xe = 0;
          if (
            (Ae.forEach((Ht) => {
              xe = Math.max(Ht.duration + Ht.delay, xe);
            }),
            d.length)
          )
            return fD(t, this._triggerName, i, r, A, p, y, [], [], m, w, xe, d);
          Ae.forEach((Ht) => {
            const Ut = Ht.element,
              ys = Lt(m, Ut, {});
            Ht.preStyleProps.forEach((Cn) => (ys[Cn] = !0));
            const oi = Lt(w, Ut, {});
            Ht.postStyleProps.forEach((Cn) => (oi[Cn] = !0)),
              Ut !== t && v.add(Ut);
          });
          const jt = Kl(v.values());
          return fD(t, this._triggerName, i, r, A, p, y, Ae, jt, m, w, xe);
        }
      }
      class FL {
        constructor(e, t, i) {
          (this.styles = e), (this.defaultParams = t), (this.normalizer = i);
        }
        buildStyles(e, t) {
          const i = {},
            r = ls(this.defaultParams);
          return (
            Object.keys(e).forEach((s) => {
              const o = e[s];
              null != o && (r[s] = o);
            }),
            this.styles.styles.forEach((s) => {
              if ("string" != typeof s) {
                const o = s;
                Object.keys(o).forEach((a) => {
                  let l = o[a];
                  l.length > 1 && (l = Wl(l, r, t));
                  const c = this.normalizer.normalizePropertyName(a, t);
                  (l = this.normalizer.normalizeStyleValue(a, c, l, t)),
                    (i[c] = l);
                });
              }
            }),
            i
          );
        }
      }
      class PL {
        constructor(e, t, i) {
          (this.name = e),
            (this.ast = t),
            (this._normalizer = i),
            (this.transitionFactories = []),
            (this.states = {}),
            t.states.forEach((r) => {
              this.states[r.name] = new FL(
                r.style,
                (r.options && r.options.params) || {},
                i
              );
            }),
            gD(this.states, "true", "1"),
            gD(this.states, "false", "0"),
            t.transitions.forEach((r) => {
              this.transitionFactories.push(new pD(e, r, this.states));
            }),
            (this.fallbackTransition = (function NL(n, e, t) {
              return new pD(
                n,
                {
                  type: 1,
                  animation: { type: 2, steps: [], options: null },
                  matchers: [(o, a) => !0],
                  options: null,
                  queryCount: 0,
                  depCount: 0,
                },
                e
              );
            })(e, this.states));
        }
        get containsQueries() {
          return this.ast.queryCount > 0;
        }
        matchTransition(e, t, i, r) {
          return (
            this.transitionFactories.find((o) => o.match(e, t, i, r)) || null
          );
        }
        matchStyles(e, t, i) {
          return this.fallbackTransition.buildStyles(e, t, i);
        }
      }
      function gD(n, e, t) {
        n.hasOwnProperty(e)
          ? n.hasOwnProperty(t) || (n[t] = n[e])
          : n.hasOwnProperty(t) && (n[e] = n[t]);
      }
      const LL = new Jl();
      class VL {
        constructor(e, t, i) {
          (this.bodyNode = e),
            (this._driver = t),
            (this._normalizer = i),
            (this._animations = {}),
            (this._playersById = {}),
            (this.players = []);
        }
        register(e, t) {
          const i = [],
            r = If(this._driver, t, i);
          if (i.length)
            throw new Error(
              `Unable to build the animation due to the following errors: ${i.join(
                "\n"
              )}`
            );
          this._animations[e] = r;
        }
        _buildPlayer(e, t, i) {
          const r = e.element,
            s = Yw(0, this._normalizer, 0, e.keyframes, t, i);
          return this._driver.animate(
            r,
            s,
            e.duration,
            e.delay,
            e.easing,
            [],
            !0
          );
        }
        create(e, t, i = {}) {
          const r = [],
            s = this._animations[e];
          let o;
          const a = new Map();
          if (
            (s
              ? ((o = Ff(this._driver, t, s, Ef, $l, {}, {}, i, LL, r)),
                o.forEach((u) => {
                  const d = Lt(a, u.element, {});
                  u.postStyleProps.forEach((h) => (d[h] = null));
                }))
              : (r.push(
                  "The requested animation doesn't exist or has already been destroyed"
                ),
                (o = [])),
            r.length)
          )
            throw new Error(
              `Unable to create the animation due to the following errors: ${r.join(
                "\n"
              )}`
            );
          a.forEach((u, d) => {
            Object.keys(u).forEach((h) => {
              u[h] = this._driver.computeStyle(d, h, ti);
            });
          });
          const c = Ei(
            o.map((u) => {
              const d = a.get(u.element);
              return this._buildPlayer(u, {}, d);
            })
          );
          return (
            (this._playersById[e] = c),
            c.onDestroy(() => this.destroy(e)),
            this.players.push(c),
            c
          );
        }
        destroy(e) {
          const t = this._getPlayer(e);
          t.destroy(), delete this._playersById[e];
          const i = this.players.indexOf(t);
          i >= 0 && this.players.splice(i, 1);
        }
        _getPlayer(e) {
          const t = this._playersById[e];
          if (!t)
            throw new Error(
              `Unable to find the timeline player referenced by ${e}`
            );
          return t;
        }
        listen(e, t, i, r) {
          const s = yf(t, "", "", "");
          return mf(this._getPlayer(e), i, s, r), () => {};
        }
        command(e, t, i, r) {
          if ("register" == i) return void this.register(e, r[0]);
          if ("create" == i) return void this.create(e, t, r[0] || {});
          const s = this._getPlayer(e);
          switch (i) {
            case "play":
              s.play();
              break;
            case "pause":
              s.pause();
              break;
            case "reset":
              s.reset();
              break;
            case "restart":
              s.restart();
              break;
            case "finish":
              s.finish();
              break;
            case "init":
              s.init();
              break;
            case "setPosition":
              s.setPosition(parseFloat(r[0]));
              break;
            case "destroy":
              this.destroy(e);
          }
        }
      }
      const mD = "ng-animate-queued",
        Lf = "ng-animate-disabled",
        $L = [],
        _D = {
          namespaceId: "",
          setForRemoval: !1,
          setForMove: !1,
          hasAnimation: !1,
          removedBeforeQueried: !1,
        },
        zL = {
          namespaceId: "",
          setForMove: !1,
          setForRemoval: !1,
          hasAnimation: !1,
          removedBeforeQueried: !0,
        },
        nn = "__ng_removed";
      class Vf {
        constructor(e, t = "") {
          this.namespaceId = t;
          const i = e && e.hasOwnProperty("value");
          if (
            ((this.value = (function KL(n) {
              return null != n ? n : null;
            })(i ? e.value : e)),
            i)
          ) {
            const s = ls(e);
            delete s.value, (this.options = s);
          } else this.options = {};
          this.options.params || (this.options.params = {});
        }
        get params() {
          return this.options.params;
        }
        absorbOptions(e) {
          const t = e.params;
          if (t) {
            const i = this.options.params;
            Object.keys(t).forEach((r) => {
              null == i[r] && (i[r] = t[r]);
            });
          }
        }
      }
      const Po = "void",
        Bf = new Vf(Po);
      class GL {
        constructor(e, t, i) {
          (this.id = e),
            (this.hostElement = t),
            (this._engine = i),
            (this.players = []),
            (this._triggers = {}),
            (this._queue = []),
            (this._elementListeners = new Map()),
            (this._hostClassName = "ng-tns-" + e),
            rn(t, this._hostClassName);
        }
        listen(e, t, i, r) {
          if (!this._triggers.hasOwnProperty(t))
            throw new Error(
              `Unable to listen on the animation trigger event "${i}" because the animation trigger "${t}" doesn't exist!`
            );
          if (null == i || 0 == i.length)
            throw new Error(
              `Unable to listen on the animation trigger "${t}" because the provided event is undefined!`
            );
          if (
            !(function YL(n) {
              return "start" == n || "done" == n;
            })(i)
          )
            throw new Error(
              `The provided animation trigger event "${i}" for the animation trigger "${t}" is not supported!`
            );
          const s = Lt(this._elementListeners, e, []),
            o = { name: t, phase: i, callback: r };
          s.push(o);
          const a = Lt(this._engine.statesByElement, e, {});
          return (
            a.hasOwnProperty(t) ||
              (rn(e, zl), rn(e, zl + "-" + t), (a[t] = Bf)),
            () => {
              this._engine.afterFlush(() => {
                const l = s.indexOf(o);
                l >= 0 && s.splice(l, 1), this._triggers[t] || delete a[t];
              });
            }
          );
        }
        register(e, t) {
          return !this._triggers[e] && ((this._triggers[e] = t), !0);
        }
        _getTrigger(e) {
          const t = this._triggers[e];
          if (!t)
            throw new Error(
              `The provided animation trigger "${e}" has not been registered!`
            );
          return t;
        }
        trigger(e, t, i, r = !0) {
          const s = this._getTrigger(t),
            o = new jf(this.id, t, e);
          let a = this._engine.statesByElement.get(e);
          a ||
            (rn(e, zl),
            rn(e, zl + "-" + t),
            this._engine.statesByElement.set(e, (a = {})));
          let l = a[t];
          const c = new Vf(i, this.id);
          if (
            (!(i && i.hasOwnProperty("value")) &&
              l &&
              c.absorbOptions(l.options),
            (a[t] = c),
            l || (l = Bf),
            c.value !== Po && l.value === c.value)
          ) {
            if (
              !(function XL(n, e) {
                const t = Object.keys(n),
                  i = Object.keys(e);
                if (t.length != i.length) return !1;
                for (let r = 0; r < t.length; r++) {
                  const s = t[r];
                  if (!e.hasOwnProperty(s) || n[s] !== e[s]) return !1;
                }
                return !0;
              })(l.params, c.params)
            ) {
              const g = [],
                y = s.matchStyles(l.value, l.params, g),
                v = s.matchStyles(c.value, c.params, g);
              g.length
                ? this._engine.reportError(g)
                : this._engine.afterFlush(() => {
                    Xi(e, y), Ln(e, v);
                  });
            }
            return;
          }
          const h = Lt(this._engine.playersByElement, e, []);
          h.forEach((g) => {
            g.namespaceId == this.id &&
              g.triggerName == t &&
              g.queued &&
              g.destroy();
          });
          let f = s.matchTransition(l.value, c.value, e, c.params),
            p = !1;
          if (!f) {
            if (!r) return;
            (f = s.fallbackTransition), (p = !0);
          }
          return (
            this._engine.totalQueuedPlayers++,
            this._queue.push({
              element: e,
              triggerName: t,
              transition: f,
              fromState: l,
              toState: c,
              player: o,
              isFallbackTransition: p,
            }),
            p ||
              (rn(e, mD),
              o.onStart(() => {
                cs(e, mD);
              })),
            o.onDone(() => {
              let g = this.players.indexOf(o);
              g >= 0 && this.players.splice(g, 1);
              const y = this._engine.playersByElement.get(e);
              if (y) {
                let v = y.indexOf(o);
                v >= 0 && y.splice(v, 1);
              }
            }),
            this.players.push(o),
            h.push(o),
            o
          );
        }
        deregister(e) {
          delete this._triggers[e],
            this._engine.statesByElement.forEach((t, i) => {
              delete t[e];
            }),
            this._elementListeners.forEach((t, i) => {
              this._elementListeners.set(
                i,
                t.filter((r) => r.name != e)
              );
            });
        }
        clearElementCache(e) {
          this._engine.statesByElement.delete(e),
            this._elementListeners.delete(e);
          const t = this._engine.playersByElement.get(e);
          t &&
            (t.forEach((i) => i.destroy()),
            this._engine.playersByElement.delete(e));
        }
        _signalRemovalForInnerTriggers(e, t) {
          const i = this._engine.driver.query(e, Gl, !0);
          i.forEach((r) => {
            if (r[nn]) return;
            const s = this._engine.fetchNamespacesByElement(r);
            s.size
              ? s.forEach((o) => o.triggerLeaveAnimation(r, t, !1, !0))
              : this.clearElementCache(r);
          }),
            this._engine.afterFlushAnimationsDone(() =>
              i.forEach((r) => this.clearElementCache(r))
            );
        }
        triggerLeaveAnimation(e, t, i, r) {
          const s = this._engine.statesByElement.get(e),
            o = new Map();
          if (s) {
            const a = [];
            if (
              (Object.keys(s).forEach((l) => {
                if ((o.set(l, s[l].value), this._triggers[l])) {
                  const c = this.trigger(e, l, Po, r);
                  c && a.push(c);
                }
              }),
              a.length)
            )
              return (
                this._engine.markElementAsRemoved(this.id, e, !0, t, o),
                i && Ei(a).onDone(() => this._engine.processLeaveNode(e)),
                !0
              );
          }
          return !1;
        }
        prepareLeaveAnimationListeners(e) {
          const t = this._elementListeners.get(e),
            i = this._engine.statesByElement.get(e);
          if (t && i) {
            const r = new Set();
            t.forEach((s) => {
              const o = s.name;
              if (r.has(o)) return;
              r.add(o);
              const l = this._triggers[o].fallbackTransition,
                c = i[o] || Bf,
                u = new Vf(Po),
                d = new jf(this.id, o, e);
              this._engine.totalQueuedPlayers++,
                this._queue.push({
                  element: e,
                  triggerName: o,
                  transition: l,
                  fromState: c,
                  toState: u,
                  player: d,
                  isFallbackTransition: !0,
                });
            });
          }
        }
        removeNode(e, t) {
          const i = this._engine;
          if (
            (e.childElementCount && this._signalRemovalForInnerTriggers(e, t),
            this.triggerLeaveAnimation(e, t, !0))
          )
            return;
          let r = !1;
          if (i.totalAnimations) {
            const s = i.players.length ? i.playersByQueriedElement.get(e) : [];
            if (s && s.length) r = !0;
            else {
              let o = e;
              for (; (o = o.parentNode); )
                if (i.statesByElement.get(o)) {
                  r = !0;
                  break;
                }
            }
          }
          if ((this.prepareLeaveAnimationListeners(e), r))
            i.markElementAsRemoved(this.id, e, !1, t);
          else {
            const s = e[nn];
            (!s || s === _D) &&
              (i.afterFlush(() => this.clearElementCache(e)),
              i.destroyInnerAnimations(e),
              i._onRemovalComplete(e, t));
          }
        }
        insertNode(e, t) {
          rn(e, this._hostClassName);
        }
        drainQueuedTransitions(e) {
          const t = [];
          return (
            this._queue.forEach((i) => {
              const r = i.player;
              if (r.destroyed) return;
              const s = i.element,
                o = this._elementListeners.get(s);
              o &&
                o.forEach((a) => {
                  if (a.name == i.triggerName) {
                    const l = yf(
                      s,
                      i.triggerName,
                      i.fromState.value,
                      i.toState.value
                    );
                    (l._data = e), mf(i.player, a.phase, l, a.callback);
                  }
                }),
                r.markedForDestroy
                  ? this._engine.afterFlush(() => {
                      r.destroy();
                    })
                  : t.push(i);
            }),
            (this._queue = []),
            t.sort((i, r) => {
              const s = i.transition.ast.depCount,
                o = r.transition.ast.depCount;
              return 0 == s || 0 == o
                ? s - o
                : this._engine.driver.containsElement(i.element, r.element)
                ? 1
                : -1;
            })
          );
        }
        destroy(e) {
          this.players.forEach((t) => t.destroy()),
            this._signalRemovalForInnerTriggers(this.hostElement, e);
        }
        elementContainsData(e) {
          let t = !1;
          return (
            this._elementListeners.has(e) && (t = !0),
            (t = !!this._queue.find((i) => i.element === e) || t),
            t
          );
        }
      }
      class qL {
        constructor(e, t, i) {
          (this.bodyNode = e),
            (this.driver = t),
            (this._normalizer = i),
            (this.players = []),
            (this.newHostElements = new Map()),
            (this.playersByElement = new Map()),
            (this.playersByQueriedElement = new Map()),
            (this.statesByElement = new Map()),
            (this.disabledNodes = new Set()),
            (this.totalAnimations = 0),
            (this.totalQueuedPlayers = 0),
            (this._namespaceLookup = {}),
            (this._namespaceList = []),
            (this._flushFns = []),
            (this._whenQuietFns = []),
            (this.namespacesByHostElement = new Map()),
            (this.collectedEnterElements = []),
            (this.collectedLeaveElements = []),
            (this.onRemovalComplete = (r, s) => {});
        }
        _onRemovalComplete(e, t) {
          this.onRemovalComplete(e, t);
        }
        get queuedPlayers() {
          const e = [];
          return (
            this._namespaceList.forEach((t) => {
              t.players.forEach((i) => {
                i.queued && e.push(i);
              });
            }),
            e
          );
        }
        createNamespace(e, t) {
          const i = new GL(e, t, this);
          return (
            this.bodyNode && this.driver.containsElement(this.bodyNode, t)
              ? this._balanceNamespaceList(i, t)
              : (this.newHostElements.set(t, i), this.collectEnterElement(t)),
            (this._namespaceLookup[e] = i)
          );
        }
        _balanceNamespaceList(e, t) {
          const i = this._namespaceList.length - 1;
          if (i >= 0) {
            let r = !1;
            for (let s = i; s >= 0; s--)
              if (
                this.driver.containsElement(
                  this._namespaceList[s].hostElement,
                  t
                )
              ) {
                this._namespaceList.splice(s + 1, 0, e), (r = !0);
                break;
              }
            r || this._namespaceList.splice(0, 0, e);
          } else this._namespaceList.push(e);
          return this.namespacesByHostElement.set(t, e), e;
        }
        register(e, t) {
          let i = this._namespaceLookup[e];
          return i || (i = this.createNamespace(e, t)), i;
        }
        registerTrigger(e, t, i) {
          let r = this._namespaceLookup[e];
          r && r.register(t, i) && this.totalAnimations++;
        }
        destroy(e, t) {
          if (!e) return;
          const i = this._fetchNamespace(e);
          this.afterFlush(() => {
            this.namespacesByHostElement.delete(i.hostElement),
              delete this._namespaceLookup[e];
            const r = this._namespaceList.indexOf(i);
            r >= 0 && this._namespaceList.splice(r, 1);
          }),
            this.afterFlushAnimationsDone(() => i.destroy(t));
        }
        _fetchNamespace(e) {
          return this._namespaceLookup[e];
        }
        fetchNamespacesByElement(e) {
          const t = new Set(),
            i = this.statesByElement.get(e);
          if (i) {
            const r = Object.keys(i);
            for (let s = 0; s < r.length; s++) {
              const o = i[r[s]].namespaceId;
              if (o) {
                const a = this._fetchNamespace(o);
                a && t.add(a);
              }
            }
          }
          return t;
        }
        trigger(e, t, i, r) {
          if (nc(t)) {
            const s = this._fetchNamespace(e);
            if (s) return s.trigger(t, i, r), !0;
          }
          return !1;
        }
        insertNode(e, t, i, r) {
          if (!nc(t)) return;
          const s = t[nn];
          if (s && s.setForRemoval) {
            (s.setForRemoval = !1), (s.setForMove = !0);
            const o = this.collectedLeaveElements.indexOf(t);
            o >= 0 && this.collectedLeaveElements.splice(o, 1);
          }
          if (e) {
            const o = this._fetchNamespace(e);
            o && o.insertNode(t, i);
          }
          r && this.collectEnterElement(t);
        }
        collectEnterElement(e) {
          this.collectedEnterElements.push(e);
        }
        markElementAsDisabled(e, t) {
          t
            ? this.disabledNodes.has(e) ||
              (this.disabledNodes.add(e), rn(e, Lf))
            : this.disabledNodes.has(e) &&
              (this.disabledNodes.delete(e), cs(e, Lf));
        }
        removeNode(e, t, i, r) {
          if (nc(t)) {
            const s = e ? this._fetchNamespace(e) : null;
            if (
              (s ? s.removeNode(t, r) : this.markElementAsRemoved(e, t, !1, r),
              i)
            ) {
              const o = this.namespacesByHostElement.get(t);
              o && o.id !== e && o.removeNode(t, r);
            }
          } else this._onRemovalComplete(t, r);
        }
        markElementAsRemoved(e, t, i, r, s) {
          this.collectedLeaveElements.push(t),
            (t[nn] = {
              namespaceId: e,
              setForRemoval: r,
              hasAnimation: i,
              removedBeforeQueried: !1,
              previousTriggersValues: s,
            });
        }
        listen(e, t, i, r, s) {
          return nc(t) ? this._fetchNamespace(e).listen(t, i, r, s) : () => {};
        }
        _buildInstruction(e, t, i, r, s) {
          return e.transition.build(
            this.driver,
            e.element,
            e.fromState.value,
            e.toState.value,
            i,
            r,
            e.fromState.options,
            e.toState.options,
            t,
            s
          );
        }
        destroyInnerAnimations(e) {
          let t = this.driver.query(e, Gl, !0);
          t.forEach((i) => this.destroyActiveAnimationsForElement(i)),
            0 != this.playersByQueriedElement.size &&
              ((t = this.driver.query(e, Mf, !0)),
              t.forEach((i) => this.finishActiveQueriedAnimationOnElement(i)));
        }
        destroyActiveAnimationsForElement(e) {
          const t = this.playersByElement.get(e);
          t &&
            t.forEach((i) => {
              i.queued ? (i.markedForDestroy = !0) : i.destroy();
            });
        }
        finishActiveQueriedAnimationOnElement(e) {
          const t = this.playersByQueriedElement.get(e);
          t && t.forEach((i) => i.finish());
        }
        whenRenderingDone() {
          return new Promise((e) => {
            if (this.players.length) return Ei(this.players).onDone(() => e());
            e();
          });
        }
        processLeaveNode(e) {
          var t;
          const i = e[nn];
          if (i && i.setForRemoval) {
            if (((e[nn] = _D), i.namespaceId)) {
              this.destroyInnerAnimations(e);
              const r = this._fetchNamespace(i.namespaceId);
              r && r.clearElementCache(e);
            }
            this._onRemovalComplete(e, i.setForRemoval);
          }
          (null === (t = e.classList) || void 0 === t
            ? void 0
            : t.contains(Lf)) && this.markElementAsDisabled(e, !1),
            this.driver.query(e, ".ng-animate-disabled", !0).forEach((r) => {
              this.markElementAsDisabled(r, !1);
            });
        }
        flush(e = -1) {
          let t = [];
          if (
            (this.newHostElements.size &&
              (this.newHostElements.forEach((i, r) =>
                this._balanceNamespaceList(i, r)
              ),
              this.newHostElements.clear()),
            this.totalAnimations && this.collectedEnterElements.length)
          )
            for (let i = 0; i < this.collectedEnterElements.length; i++)
              rn(this.collectedEnterElements[i], "ng-star-inserted");
          if (
            this._namespaceList.length &&
            (this.totalQueuedPlayers || this.collectedLeaveElements.length)
          ) {
            const i = [];
            try {
              t = this._flushAnimations(i, e);
            } finally {
              for (let r = 0; r < i.length; r++) i[r]();
            }
          } else
            for (let i = 0; i < this.collectedLeaveElements.length; i++)
              this.processLeaveNode(this.collectedLeaveElements[i]);
          if (
            ((this.totalQueuedPlayers = 0),
            (this.collectedEnterElements.length = 0),
            (this.collectedLeaveElements.length = 0),
            this._flushFns.forEach((i) => i()),
            (this._flushFns = []),
            this._whenQuietFns.length)
          ) {
            const i = this._whenQuietFns;
            (this._whenQuietFns = []),
              t.length
                ? Ei(t).onDone(() => {
                    i.forEach((r) => r());
                  })
                : i.forEach((r) => r());
          }
        }
        reportError(e) {
          throw new Error(
            `Unable to process animations due to the following failed trigger transitions\n ${e.join(
              "\n"
            )}`
          );
        }
        _flushAnimations(e, t) {
          const i = new Jl(),
            r = [],
            s = new Map(),
            o = [],
            a = new Map(),
            l = new Map(),
            c = new Map(),
            u = new Set();
          this.disabledNodes.forEach((O) => {
            u.add(O);
            const R = this.driver.query(O, ".ng-animate-queued", !0);
            for (let N = 0; N < R.length; N++) u.add(R[N]);
          });
          const d = this.bodyNode,
            h = Array.from(this.statesByElement.keys()),
            f = bD(h, this.collectedEnterElements),
            p = new Map();
          let g = 0;
          f.forEach((O, R) => {
            const N = Ef + g++;
            p.set(R, N), O.forEach((oe) => rn(oe, N));
          });
          const y = [],
            v = new Set(),
            m = new Set();
          for (let O = 0; O < this.collectedLeaveElements.length; O++) {
            const R = this.collectedLeaveElements[O],
              N = R[nn];
            N &&
              N.setForRemoval &&
              (y.push(R),
              v.add(R),
              N.hasAnimation
                ? this.driver
                    .query(R, ".ng-star-inserted", !0)
                    .forEach((oe) => v.add(oe))
                : m.add(R));
          }
          const w = new Map(),
            A = bD(h, Array.from(v));
          A.forEach((O, R) => {
            const N = $l + g++;
            w.set(R, N), O.forEach((oe) => rn(oe, N));
          }),
            e.push(() => {
              f.forEach((O, R) => {
                const N = p.get(R);
                O.forEach((oe) => cs(oe, N));
              }),
                A.forEach((O, R) => {
                  const N = w.get(R);
                  O.forEach((oe) => cs(oe, N));
                }),
                y.forEach((O) => {
                  this.processLeaveNode(O);
                });
            });
          const $ = [],
            Ae = [];
          for (let O = this._namespaceList.length - 1; O >= 0; O--)
            this._namespaceList[O].drainQueuedTransitions(t).forEach((N) => {
              const oe = N.player,
                it = N.element;
              if (($.push(oe), this.collectedEnterElements.length)) {
                const bt = it[nn];
                if (bt && bt.setForMove) {
                  if (
                    bt.previousTriggersValues &&
                    bt.previousTriggersValues.has(N.triggerName)
                  ) {
                    const sr = bt.previousTriggersValues.get(N.triggerName),
                      Ii = this.statesByElement.get(N.element);
                    Ii && Ii[N.triggerName] && (Ii[N.triggerName].value = sr);
                  }
                  return void oe.destroy();
                }
              }
              const jn = !d || !this.driver.containsElement(d, it),
                $t = w.get(it),
                Oi = p.get(it),
                ke = this._buildInstruction(N, i, Oi, $t, jn);
              if (ke.errors && ke.errors.length) return void Ae.push(ke);
              if (jn)
                return (
                  oe.onStart(() => Xi(it, ke.fromStyles)),
                  oe.onDestroy(() => Ln(it, ke.toStyles)),
                  void r.push(oe)
                );
              if (N.isFallbackTransition)
                return (
                  oe.onStart(() => Xi(it, ke.fromStyles)),
                  oe.onDestroy(() => Ln(it, ke.toStyles)),
                  void r.push(oe)
                );
              const YM = [];
              ke.timelines.forEach((bt) => {
                (bt.stretchStartingKeyframe = !0),
                  this.disabledNodes.has(bt.element) || YM.push(bt);
              }),
                (ke.timelines = YM),
                i.append(it, ke.timelines),
                o.push({ instruction: ke, player: oe, element: it }),
                ke.queriedElements.forEach((bt) => Lt(a, bt, []).push(oe)),
                ke.preStyleProps.forEach((bt, sr) => {
                  const Ii = Object.keys(bt);
                  if (Ii.length) {
                    let or = l.get(sr);
                    or || l.set(sr, (or = new Set())),
                      Ii.forEach((Op) => or.add(Op));
                  }
                }),
                ke.postStyleProps.forEach((bt, sr) => {
                  const Ii = Object.keys(bt);
                  let or = c.get(sr);
                  or || c.set(sr, (or = new Set())),
                    Ii.forEach((Op) => or.add(Op));
                });
            });
          if (Ae.length) {
            const O = [];
            Ae.forEach((R) => {
              O.push(`@${R.triggerName} has failed due to:\n`),
                R.errors.forEach((N) => O.push(`- ${N}\n`));
            }),
              $.forEach((R) => R.destroy()),
              this.reportError(O);
          }
          const xe = new Map(),
            jt = new Map();
          o.forEach((O) => {
            const R = O.element;
            i.has(R) &&
              (jt.set(R, R),
              this._beforeAnimationBuild(
                O.player.namespaceId,
                O.instruction,
                xe
              ));
          }),
            r.forEach((O) => {
              const R = O.element;
              this._getPreviousPlayers(
                R,
                !1,
                O.namespaceId,
                O.triggerName,
                null
              ).forEach((oe) => {
                Lt(xe, R, []).push(oe), oe.destroy();
              });
            });
          const Ht = y.filter((O) => wD(O, l, c)),
            Ut = new Map();
          vD(Ut, this.driver, m, c, ti).forEach((O) => {
            wD(O, l, c) && Ht.push(O);
          });
          const oi = new Map();
          f.forEach((O, R) => {
            vD(oi, this.driver, new Set(O), l, "!");
          }),
            Ht.forEach((O) => {
              const R = Ut.get(O),
                N = oi.get(O);
              Ut.set(O, Object.assign(Object.assign({}, R), N));
            });
          const Cn = [],
            vs = [],
            bs = {};
          o.forEach((O) => {
            const { element: R, player: N, instruction: oe } = O;
            if (i.has(R)) {
              if (u.has(R))
                return (
                  N.onDestroy(() => Ln(R, oe.toStyles)),
                  (N.disabled = !0),
                  N.overrideTotalTime(oe.totalTime),
                  void r.push(N)
                );
              let it = bs;
              if (jt.size > 1) {
                let $t = R;
                const Oi = [];
                for (; ($t = $t.parentNode); ) {
                  const ke = jt.get($t);
                  if (ke) {
                    it = ke;
                    break;
                  }
                  Oi.push($t);
                }
                Oi.forEach((ke) => jt.set(ke, it));
              }
              const jn = this._buildAnimation(N.namespaceId, oe, xe, s, oi, Ut);
              if ((N.setRealPlayer(jn), it === bs)) Cn.push(N);
              else {
                const $t = this.playersByElement.get(it);
                $t && $t.length && (N.parentPlayer = Ei($t)), r.push(N);
              }
            } else
              Xi(R, oe.fromStyles),
                N.onDestroy(() => Ln(R, oe.toStyles)),
                vs.push(N),
                u.has(R) && r.push(N);
          }),
            vs.forEach((O) => {
              const R = s.get(O.element);
              if (R && R.length) {
                const N = Ei(R);
                O.setRealPlayer(N);
              }
            }),
            r.forEach((O) => {
              O.parentPlayer ? O.syncPlayerEvents(O.parentPlayer) : O.destroy();
            });
          for (let O = 0; O < y.length; O++) {
            const R = y[O],
              N = R[nn];
            if ((cs(R, $l), N && N.hasAnimation)) continue;
            let oe = [];
            if (a.size) {
              let jn = a.get(R);
              jn && jn.length && oe.push(...jn);
              let $t = this.driver.query(R, Mf, !0);
              for (let Oi = 0; Oi < $t.length; Oi++) {
                let ke = a.get($t[Oi]);
                ke && ke.length && oe.push(...ke);
              }
            }
            const it = oe.filter((jn) => !jn.destroyed);
            it.length ? ZL(this, R, it) : this.processLeaveNode(R);
          }
          return (
            (y.length = 0),
            Cn.forEach((O) => {
              this.players.push(O),
                O.onDone(() => {
                  O.destroy();
                  const R = this.players.indexOf(O);
                  this.players.splice(R, 1);
                }),
                O.play();
            }),
            Cn
          );
        }
        elementContainsData(e, t) {
          let i = !1;
          const r = t[nn];
          return (
            r && r.setForRemoval && (i = !0),
            this.playersByElement.has(t) && (i = !0),
            this.playersByQueriedElement.has(t) && (i = !0),
            this.statesByElement.has(t) && (i = !0),
            this._fetchNamespace(e).elementContainsData(t) || i
          );
        }
        afterFlush(e) {
          this._flushFns.push(e);
        }
        afterFlushAnimationsDone(e) {
          this._whenQuietFns.push(e);
        }
        _getPreviousPlayers(e, t, i, r, s) {
          let o = [];
          if (t) {
            const a = this.playersByQueriedElement.get(e);
            a && (o = a);
          } else {
            const a = this.playersByElement.get(e);
            if (a) {
              const l = !s || s == Po;
              a.forEach((c) => {
                c.queued || (!l && c.triggerName != r) || o.push(c);
              });
            }
          }
          return (
            (i || r) &&
              (o = o.filter(
                (a) => !((i && i != a.namespaceId) || (r && r != a.triggerName))
              )),
            o
          );
        }
        _beforeAnimationBuild(e, t, i) {
          const s = t.element,
            o = t.isRemovalTransition ? void 0 : e,
            a = t.isRemovalTransition ? void 0 : t.triggerName;
          for (const l of t.timelines) {
            const c = l.element,
              u = c !== s,
              d = Lt(i, c, []);
            this._getPreviousPlayers(c, u, o, a, t.toState).forEach((f) => {
              const p = f.getRealPlayer();
              p.beforeDestroy && p.beforeDestroy(), f.destroy(), d.push(f);
            });
          }
          Xi(s, t.fromStyles);
        }
        _buildAnimation(e, t, i, r, s, o) {
          const a = t.triggerName,
            l = t.element,
            c = [],
            u = new Set(),
            d = new Set(),
            h = t.timelines.map((p) => {
              const g = p.element;
              u.add(g);
              const y = g[nn];
              if (y && y.removedBeforeQueried)
                return new as(p.duration, p.delay);
              const v = g !== l,
                m = (function QL(n) {
                  const e = [];
                  return CD(n, e), e;
                })((i.get(g) || $L).map((xe) => xe.getRealPlayer())).filter(
                  (xe) => !!xe.element && xe.element === g
                ),
                w = s.get(g),
                A = o.get(g),
                $ = Yw(0, this._normalizer, 0, p.keyframes, w, A),
                Ae = this._buildPlayer(p, $, m);
              if ((p.subTimeline && r && d.add(g), v)) {
                const xe = new jf(e, a, g);
                xe.setRealPlayer(Ae), c.push(xe);
              }
              return Ae;
            });
          c.forEach((p) => {
            Lt(this.playersByQueriedElement, p.element, []).push(p),
              p.onDone(() =>
                (function WL(n, e, t) {
                  let i;
                  if (n instanceof Map) {
                    if (((i = n.get(e)), i)) {
                      if (i.length) {
                        const r = i.indexOf(t);
                        i.splice(r, 1);
                      }
                      0 == i.length && n.delete(e);
                    }
                  } else if (((i = n[e]), i)) {
                    if (i.length) {
                      const r = i.indexOf(t);
                      i.splice(r, 1);
                    }
                    0 == i.length && delete n[e];
                  }
                  return i;
                })(this.playersByQueriedElement, p.element, p)
              );
          }),
            u.forEach((p) => rn(p, nD));
          const f = Ei(h);
          return (
            f.onDestroy(() => {
              u.forEach((p) => cs(p, nD)), Ln(l, t.toStyles);
            }),
            d.forEach((p) => {
              Lt(r, p, []).push(f);
            }),
            f
          );
        }
        _buildPlayer(e, t, i) {
          return t.length > 0
            ? this.driver.animate(
                e.element,
                t,
                e.duration,
                e.delay,
                e.easing,
                i
              )
            : new as(e.duration, e.delay);
        }
      }
      class jf {
        constructor(e, t, i) {
          (this.namespaceId = e),
            (this.triggerName = t),
            (this.element = i),
            (this._player = new as()),
            (this._containsRealPlayer = !1),
            (this._queuedCallbacks = {}),
            (this.destroyed = !1),
            (this.markedForDestroy = !1),
            (this.disabled = !1),
            (this.queued = !0),
            (this.totalTime = 0);
        }
        setRealPlayer(e) {
          this._containsRealPlayer ||
            ((this._player = e),
            Object.keys(this._queuedCallbacks).forEach((t) => {
              this._queuedCallbacks[t].forEach((i) => mf(e, t, void 0, i));
            }),
            (this._queuedCallbacks = {}),
            (this._containsRealPlayer = !0),
            this.overrideTotalTime(e.totalTime),
            (this.queued = !1));
        }
        getRealPlayer() {
          return this._player;
        }
        overrideTotalTime(e) {
          this.totalTime = e;
        }
        syncPlayerEvents(e) {
          const t = this._player;
          t.triggerCallback && e.onStart(() => t.triggerCallback("start")),
            e.onDone(() => this.finish()),
            e.onDestroy(() => this.destroy());
        }
        _queueEvent(e, t) {
          Lt(this._queuedCallbacks, e, []).push(t);
        }
        onDone(e) {
          this.queued && this._queueEvent("done", e), this._player.onDone(e);
        }
        onStart(e) {
          this.queued && this._queueEvent("start", e), this._player.onStart(e);
        }
        onDestroy(e) {
          this.queued && this._queueEvent("destroy", e),
            this._player.onDestroy(e);
        }
        init() {
          this._player.init();
        }
        hasStarted() {
          return !this.queued && this._player.hasStarted();
        }
        play() {
          !this.queued && this._player.play();
        }
        pause() {
          !this.queued && this._player.pause();
        }
        restart() {
          !this.queued && this._player.restart();
        }
        finish() {
          this._player.finish();
        }
        destroy() {
          (this.destroyed = !0), this._player.destroy();
        }
        reset() {
          !this.queued && this._player.reset();
        }
        setPosition(e) {
          this.queued || this._player.setPosition(e);
        }
        getPosition() {
          return this.queued ? 0 : this._player.getPosition();
        }
        triggerCallback(e) {
          const t = this._player;
          t.triggerCallback && t.triggerCallback(e);
        }
      }
      function nc(n) {
        return n && 1 === n.nodeType;
      }
      function yD(n, e) {
        const t = n.style.display;
        return (n.style.display = null != e ? e : "none"), t;
      }
      function vD(n, e, t, i, r) {
        const s = [];
        t.forEach((l) => s.push(yD(l)));
        const o = [];
        i.forEach((l, c) => {
          const u = {};
          l.forEach((d) => {
            const h = (u[d] = e.computeStyle(c, d, r));
            (!h || 0 == h.length) && ((c[nn] = zL), o.push(c));
          }),
            n.set(c, u);
        });
        let a = 0;
        return t.forEach((l) => yD(l, s[a++])), o;
      }
      function bD(n, e) {
        const t = new Map();
        if ((n.forEach((a) => t.set(a, [])), 0 == e.length)) return t;
        const r = new Set(e),
          s = new Map();
        function o(a) {
          if (!a) return 1;
          let l = s.get(a);
          if (l) return l;
          const c = a.parentNode;
          return (l = t.has(c) ? c : r.has(c) ? 1 : o(c)), s.set(a, l), l;
        }
        return (
          e.forEach((a) => {
            const l = o(a);
            1 !== l && t.get(l).push(a);
          }),
          t
        );
      }
      function rn(n, e) {
        var t;
        null === (t = n.classList) || void 0 === t || t.add(e);
      }
      function cs(n, e) {
        var t;
        null === (t = n.classList) || void 0 === t || t.remove(e);
      }
      function ZL(n, e, t) {
        Ei(t).onDone(() => n.processLeaveNode(e));
      }
      function CD(n, e) {
        for (let t = 0; t < n.length; t++) {
          const i = n[t];
          i instanceof Ww ? CD(i.players, e) : e.push(i);
        }
      }
      function wD(n, e, t) {
        const i = t.get(n);
        if (!i) return !1;
        let r = e.get(n);
        return r ? i.forEach((s) => r.add(s)) : e.set(n, i), t.delete(n), !0;
      }
      class ic {
        constructor(e, t, i) {
          (this.bodyNode = e),
            (this._driver = t),
            (this._normalizer = i),
            (this._triggerCache = {}),
            (this.onRemovalComplete = (r, s) => {}),
            (this._transitionEngine = new qL(e, t, i)),
            (this._timelineEngine = new VL(e, t, i)),
            (this._transitionEngine.onRemovalComplete = (r, s) =>
              this.onRemovalComplete(r, s));
        }
        registerTrigger(e, t, i, r, s) {
          const o = e + "-" + r;
          let a = this._triggerCache[o];
          if (!a) {
            const l = [],
              c = If(this._driver, s, l);
            if (l.length)
              throw new Error(
                `The animation trigger "${r}" has failed to build due to the following errors:\n - ${l.join(
                  "\n - "
                )}`
              );
            (a = (function RL(n, e, t) {
              return new PL(n, e, t);
            })(r, c, this._normalizer)),
              (this._triggerCache[o] = a);
          }
          this._transitionEngine.registerTrigger(t, r, a);
        }
        register(e, t) {
          this._transitionEngine.register(e, t);
        }
        destroy(e, t) {
          this._transitionEngine.destroy(e, t);
        }
        onInsert(e, t, i, r) {
          this._transitionEngine.insertNode(e, t, i, r);
        }
        onRemove(e, t, i, r) {
          this._transitionEngine.removeNode(e, t, r || !1, i);
        }
        disableAnimations(e, t) {
          this._transitionEngine.markElementAsDisabled(e, t);
        }
        process(e, t, i, r) {
          if ("@" == i.charAt(0)) {
            const [s, o] = Zw(i);
            this._timelineEngine.command(s, t, o, r);
          } else this._transitionEngine.trigger(e, t, i, r);
        }
        listen(e, t, i, r, s) {
          if ("@" == i.charAt(0)) {
            const [o, a] = Zw(i);
            return this._timelineEngine.listen(o, t, a, s);
          }
          return this._transitionEngine.listen(e, t, i, r, s);
        }
        flush(e = -1) {
          this._transitionEngine.flush(e);
        }
        get players() {
          return this._transitionEngine.players.concat(
            this._timelineEngine.players
          );
        }
        whenRenderingDone() {
          return this._transitionEngine.whenRenderingDone();
        }
      }
      function DD(n, e) {
        let t = null,
          i = null;
        return (
          Array.isArray(e) && e.length
            ? ((t = Hf(e[0])), e.length > 1 && (i = Hf(e[e.length - 1])))
            : e && (t = Hf(e)),
          t || i ? new JL(n, t, i) : null
        );
      }
      let JL = (() => {
        class n {
          constructor(t, i, r) {
            (this._element = t),
              (this._startStyles = i),
              (this._endStyles = r),
              (this._state = 0);
            let s = n.initialStylesByElement.get(t);
            s || n.initialStylesByElement.set(t, (s = {})),
              (this._initialStyles = s);
          }
          start() {
            this._state < 1 &&
              (this._startStyles &&
                Ln(this._element, this._startStyles, this._initialStyles),
              (this._state = 1));
          }
          finish() {
            this.start(),
              this._state < 2 &&
                (Ln(this._element, this._initialStyles),
                this._endStyles &&
                  (Ln(this._element, this._endStyles),
                  (this._endStyles = null)),
                (this._state = 1));
          }
          destroy() {
            this.finish(),
              this._state < 3 &&
                (n.initialStylesByElement.delete(this._element),
                this._startStyles &&
                  (Xi(this._element, this._startStyles),
                  (this._endStyles = null)),
                this._endStyles &&
                  (Xi(this._element, this._endStyles),
                  (this._endStyles = null)),
                Ln(this._element, this._initialStyles),
                (this._state = 3));
          }
        }
        return (n.initialStylesByElement = new WeakMap()), n;
      })();
      function Hf(n) {
        let e = null;
        const t = Object.keys(n);
        for (let i = 0; i < t.length; i++) {
          const r = t[i];
          eV(r) && ((e = e || {}), (e[r] = n[r]));
        }
        return e;
      }
      function eV(n) {
        return "display" === n || "position" === n;
      }
      const ED = "animation",
        MD = "animationend";
      class iV {
        constructor(e, t, i, r, s, o, a) {
          (this._element = e),
            (this._name = t),
            (this._duration = i),
            (this._delay = r),
            (this._easing = s),
            (this._fillMode = o),
            (this._onDoneFn = a),
            (this._finished = !1),
            (this._destroyed = !1),
            (this._startTime = 0),
            (this._position = 0),
            (this._eventFn = (l) => this._handleCallback(l));
        }
        apply() {
          (function rV(n, e) {
            const t = $f(n, "").trim();
            let i = 0;
            t.length &&
              ((i =
                (function oV(n, e) {
                  let t = 0;
                  for (let i = 0; i < n.length; i++) n.charAt(i) === e && t++;
                  return t;
                })(t, ",") + 1),
              (e = `${t}, ${e}`)),
              rc(n, "", e);
          })(
            this._element,
            `${this._duration}ms ${this._easing} ${this._delay}ms 1 normal ${this._fillMode} ${this._name}`
          ),
            TD(this._element, this._eventFn, !1),
            (this._startTime = Date.now());
        }
        pause() {
          SD(this._element, this._name, "paused");
        }
        resume() {
          SD(this._element, this._name, "running");
        }
        setPosition(e) {
          const t = AD(this._element, this._name);
          (this._position = e * this._duration),
            rc(this._element, "Delay", `-${this._position}ms`, t);
        }
        getPosition() {
          return this._position;
        }
        _handleCallback(e) {
          const t = e._ngTestManualTimestamp || Date.now(),
            i = 1e3 * parseFloat(e.elapsedTime.toFixed(3));
          e.animationName == this._name &&
            Math.max(t - this._startTime, 0) >= this._delay &&
            i >= this._duration &&
            this.finish();
        }
        finish() {
          this._finished ||
            ((this._finished = !0),
            this._onDoneFn(),
            TD(this._element, this._eventFn, !0));
        }
        destroy() {
          this._destroyed ||
            ((this._destroyed = !0),
            this.finish(),
            (function sV(n, e) {
              const i = $f(n, "").split(","),
                r = Uf(i, e);
              r >= 0 && (i.splice(r, 1), rc(n, "", i.join(",")));
            })(this._element, this._name));
        }
      }
      function SD(n, e, t) {
        rc(n, "PlayState", t, AD(n, e));
      }
      function AD(n, e) {
        const t = $f(n, "");
        return t.indexOf(",") > 0 ? Uf(t.split(","), e) : Uf([t], e);
      }
      function Uf(n, e) {
        for (let t = 0; t < n.length; t++) if (n[t].indexOf(e) >= 0) return t;
        return -1;
      }
      function TD(n, e, t) {
        t ? n.removeEventListener(MD, e) : n.addEventListener(MD, e);
      }
      function rc(n, e, t, i) {
        const r = ED + e;
        if (null != i) {
          const s = n.style[r];
          if (s.length) {
            const o = s.split(",");
            (o[i] = t), (t = o.join(","));
          }
        }
        n.style[r] = t;
      }
      function $f(n, e) {
        return n.style[ED + e] || "";
      }
      class OD {
        constructor(e, t, i, r, s, o, a, l) {
          (this.element = e),
            (this.keyframes = t),
            (this.animationName = i),
            (this._duration = r),
            (this._delay = s),
            (this._finalStyles = a),
            (this._specialStyles = l),
            (this._onDoneFns = []),
            (this._onStartFns = []),
            (this._onDestroyFns = []),
            (this.currentSnapshot = {}),
            (this._state = 0),
            (this.easing = o || "linear"),
            (this.totalTime = r + s),
            this._buildStyler();
        }
        onStart(e) {
          this._onStartFns.push(e);
        }
        onDone(e) {
          this._onDoneFns.push(e);
        }
        onDestroy(e) {
          this._onDestroyFns.push(e);
        }
        destroy() {
          this.init(),
            !(this._state >= 4) &&
              ((this._state = 4),
              this._styler.destroy(),
              this._flushStartFns(),
              this._flushDoneFns(),
              this._specialStyles && this._specialStyles.destroy(),
              this._onDestroyFns.forEach((e) => e()),
              (this._onDestroyFns = []));
        }
        _flushDoneFns() {
          this._onDoneFns.forEach((e) => e()), (this._onDoneFns = []);
        }
        _flushStartFns() {
          this._onStartFns.forEach((e) => e()), (this._onStartFns = []);
        }
        finish() {
          this.init(),
            !(this._state >= 3) &&
              ((this._state = 3),
              this._styler.finish(),
              this._flushStartFns(),
              this._specialStyles && this._specialStyles.finish(),
              this._flushDoneFns());
        }
        setPosition(e) {
          this._styler.setPosition(e);
        }
        getPosition() {
          return this._styler.getPosition();
        }
        hasStarted() {
          return this._state >= 2;
        }
        init() {
          this._state >= 1 ||
            ((this._state = 1),
            this._styler.apply(),
            this._delay && this._styler.pause());
        }
        play() {
          this.init(),
            this.hasStarted() ||
              (this._flushStartFns(),
              (this._state = 2),
              this._specialStyles && this._specialStyles.start()),
            this._styler.resume();
        }
        pause() {
          this.init(), this._styler.pause();
        }
        restart() {
          this.reset(), this.play();
        }
        reset() {
          (this._state = 0),
            this._styler.destroy(),
            this._buildStyler(),
            this._styler.apply();
        }
        _buildStyler() {
          this._styler = new iV(
            this.element,
            this.animationName,
            this._duration,
            this._delay,
            this.easing,
            "forwards",
            () => this.finish()
          );
        }
        triggerCallback(e) {
          const t = "start" == e ? this._onStartFns : this._onDoneFns;
          t.forEach((i) => i()), (t.length = 0);
        }
        beforeDestroy() {
          this.init();
          const e = {};
          if (this.hasStarted()) {
            const t = this._state >= 3;
            Object.keys(this._finalStyles).forEach((i) => {
              "offset" != i &&
                (e[i] = t ? this._finalStyles[i] : Of(this.element, i));
            });
          }
          this.currentSnapshot = e;
        }
      }
      class cV extends as {
        constructor(e, t) {
          super(),
            (this.element = e),
            (this._startingStyles = {}),
            (this.__initialized = !1),
            (this._styles = Jw(t));
        }
        init() {
          this.__initialized ||
            !this._startingStyles ||
            ((this.__initialized = !0),
            Object.keys(this._styles).forEach((e) => {
              this._startingStyles[e] = this.element.style[e];
            }),
            super.init());
        }
        play() {
          !this._startingStyles ||
            (this.init(),
            Object.keys(this._styles).forEach((e) =>
              this.element.style.setProperty(e, this._styles[e])
            ),
            super.play());
        }
        destroy() {
          !this._startingStyles ||
            (Object.keys(this._startingStyles).forEach((e) => {
              const t = this._startingStyles[e];
              t
                ? this.element.style.setProperty(e, t)
                : this.element.style.removeProperty(e);
            }),
            (this._startingStyles = null),
            super.destroy());
        }
      }
      class xD {
        constructor() {
          this._count = 0;
        }
        validateStyleProperty(e) {
          return bf(e);
        }
        matchesElement(e, t) {
          return !1;
        }
        containsElement(e, t) {
          return Cf(e, t);
        }
        query(e, t, i) {
          return wf(e, t, i);
        }
        computeStyle(e, t, i) {
          return window.getComputedStyle(e)[t];
        }
        buildKeyframeElement(e, t, i) {
          i = i.map((a) => Jw(a));
          let r = `@keyframes ${t} {\n`,
            s = "";
          i.forEach((a) => {
            s = " ";
            const l = parseFloat(a.offset);
            (r += `${s}${100 * l}% {\n`),
              (s += " "),
              Object.keys(a).forEach((c) => {
                const u = a[c];
                switch (c) {
                  case "offset":
                    return;
                  case "easing":
                    return void (
                      u && (r += `${s}animation-timing-function: ${u};\n`)
                    );
                  default:
                    return void (r += `${s}${c}: ${u};\n`);
                }
              }),
              (r += `${s}}\n`);
          }),
            (r += "}\n");
          const o = document.createElement("style");
          return (o.textContent = r), o;
        }
        animate(e, t, i, r, s, o = [], a) {
          const l = o.filter((y) => y instanceof OD),
            c = {};
          aD(i, r) &&
            l.forEach((y) => {
              let v = y.currentSnapshot;
              Object.keys(v).forEach((m) => (c[m] = v[m]));
            });
          const u = (function hV(n) {
            let e = {};
            return (
              n &&
                (Array.isArray(n) ? n : [n]).forEach((i) => {
                  Object.keys(i).forEach((r) => {
                    "offset" == r || "easing" == r || (e[r] = i[r]);
                  });
                }),
              e
            );
          })((t = lD(e, t, c)));
          if (0 == i) return new cV(e, u);
          const d = "gen_css_kf_" + this._count++,
            h = this.buildKeyframeElement(e, d, t);
          (function dV(n) {
            var e;
            const t =
              null === (e = n.getRootNode) || void 0 === e ? void 0 : e.call(n);
            return "undefined" != typeof ShadowRoot && t instanceof ShadowRoot
              ? t
              : document.head;
          })(e).appendChild(h);
          const p = DD(e, t),
            g = new OD(e, t, d, i, r, s, u, p);
          return (
            g.onDestroy(() =>
              (function fV(n) {
                n.parentNode.removeChild(n);
              })(h)
            ),
            g
          );
        }
      }
      class FD {
        constructor(e, t, i, r) {
          (this.element = e),
            (this.keyframes = t),
            (this.options = i),
            (this._specialStyles = r),
            (this._onDoneFns = []),
            (this._onStartFns = []),
            (this._onDestroyFns = []),
            (this._initialized = !1),
            (this._finished = !1),
            (this._started = !1),
            (this._destroyed = !1),
            (this.time = 0),
            (this.parentPlayer = null),
            (this.currentSnapshot = {}),
            (this._duration = i.duration),
            (this._delay = i.delay || 0),
            (this.time = this._duration + this._delay);
        }
        _onFinish() {
          this._finished ||
            ((this._finished = !0),
            this._onDoneFns.forEach((e) => e()),
            (this._onDoneFns = []));
        }
        init() {
          this._buildPlayer(), this._preparePlayerBeforeStart();
        }
        _buildPlayer() {
          if (this._initialized) return;
          this._initialized = !0;
          const e = this.keyframes;
          (this.domPlayer = this._triggerWebAnimation(
            this.element,
            e,
            this.options
          )),
            (this._finalKeyframe = e.length ? e[e.length - 1] : {}),
            this.domPlayer.addEventListener("finish", () => this._onFinish());
        }
        _preparePlayerBeforeStart() {
          this._delay ? this._resetDomPlayerState() : this.domPlayer.pause();
        }
        _triggerWebAnimation(e, t, i) {
          return e.animate(t, i);
        }
        onStart(e) {
          this._onStartFns.push(e);
        }
        onDone(e) {
          this._onDoneFns.push(e);
        }
        onDestroy(e) {
          this._onDestroyFns.push(e);
        }
        play() {
          this._buildPlayer(),
            this.hasStarted() ||
              (this._onStartFns.forEach((e) => e()),
              (this._onStartFns = []),
              (this._started = !0),
              this._specialStyles && this._specialStyles.start()),
            this.domPlayer.play();
        }
        pause() {
          this.init(), this.domPlayer.pause();
        }
        finish() {
          this.init(),
            this._specialStyles && this._specialStyles.finish(),
            this._onFinish(),
            this.domPlayer.finish();
        }
        reset() {
          this._resetDomPlayerState(),
            (this._destroyed = !1),
            (this._finished = !1),
            (this._started = !1);
        }
        _resetDomPlayerState() {
          this.domPlayer && this.domPlayer.cancel();
        }
        restart() {
          this.reset(), this.play();
        }
        hasStarted() {
          return this._started;
        }
        destroy() {
          this._destroyed ||
            ((this._destroyed = !0),
            this._resetDomPlayerState(),
            this._onFinish(),
            this._specialStyles && this._specialStyles.destroy(),
            this._onDestroyFns.forEach((e) => e()),
            (this._onDestroyFns = []));
        }
        setPosition(e) {
          void 0 === this.domPlayer && this.init(),
            (this.domPlayer.currentTime = e * this.time);
        }
        getPosition() {
          return this.domPlayer.currentTime / this.time;
        }
        get totalTime() {
          return this._delay + this._duration;
        }
        beforeDestroy() {
          const e = {};
          if (this.hasStarted()) {
            const t = this._finalKeyframe;
            Object.keys(t).forEach((i) => {
              "offset" != i &&
                (e[i] = this._finished ? t[i] : Of(this.element, i));
            });
          }
          this.currentSnapshot = e;
        }
        triggerCallback(e) {
          const t = "start" == e ? this._onStartFns : this._onDoneFns;
          t.forEach((i) => i()), (t.length = 0);
        }
      }
      class pV {
        constructor() {
          (this._isNativeImpl = /\{\s*\[native\s+code\]\s*\}/.test(
            RD().toString()
          )),
            (this._cssKeyframesDriver = new xD());
        }
        validateStyleProperty(e) {
          return bf(e);
        }
        matchesElement(e, t) {
          return !1;
        }
        containsElement(e, t) {
          return Cf(e, t);
        }
        query(e, t, i) {
          return wf(e, t, i);
        }
        computeStyle(e, t, i) {
          return window.getComputedStyle(e)[t];
        }
        overrideWebAnimationsSupport(e) {
          this._isNativeImpl = e;
        }
        animate(e, t, i, r, s, o = [], a) {
          if (!a && !this._isNativeImpl)
            return this._cssKeyframesDriver.animate(e, t, i, r, s, o);
          const u = {
            duration: i,
            delay: r,
            fill: 0 == r ? "both" : "forwards",
          };
          s && (u.easing = s);
          const d = {},
            h = o.filter((p) => p instanceof FD);
          aD(i, r) &&
            h.forEach((p) => {
              let g = p.currentSnapshot;
              Object.keys(g).forEach((y) => (d[y] = g[y]));
            });
          const f = DD(e, (t = lD(e, (t = t.map((p) => Mi(p, !1))), d)));
          return new FD(e, t, u, f);
        }
      }
      function RD() {
        return (Kw() && Element.prototype.animate) || {};
      }
      let mV = (() => {
        class n extends zw {
          constructor(t, i) {
            super(),
              (this._nextAnimationId = 0),
              (this._renderer = t.createRenderer(i.body, {
                id: "0",
                encapsulation: an.None,
                styles: [],
                data: { animation: [] },
              }));
          }
          build(t) {
            const i = this._nextAnimationId.toString();
            this._nextAnimationId++;
            const r = Array.isArray(t) ? Gw(t) : t;
            return (
              PD(this._renderer, null, i, "register", [r]),
              new _V(i, this._renderer)
            );
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(ao), b(ue));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      class _V extends class eL {} {
        constructor(e, t) {
          super(), (this._id = e), (this._renderer = t);
        }
        create(e, t) {
          return new yV(this._id, e, t || {}, this._renderer);
        }
      }
      class yV {
        constructor(e, t, i, r) {
          (this.id = e),
            (this.element = t),
            (this._renderer = r),
            (this.parentPlayer = null),
            (this._started = !1),
            (this.totalTime = 0),
            this._command("create", i);
        }
        _listen(e, t) {
          return this._renderer.listen(this.element, `@@${this.id}:${e}`, t);
        }
        _command(e, ...t) {
          return PD(this._renderer, this.element, this.id, e, t);
        }
        onDone(e) {
          this._listen("done", e);
        }
        onStart(e) {
          this._listen("start", e);
        }
        onDestroy(e) {
          this._listen("destroy", e);
        }
        init() {
          this._command("init");
        }
        hasStarted() {
          return this._started;
        }
        play() {
          this._command("play"), (this._started = !0);
        }
        pause() {
          this._command("pause");
        }
        restart() {
          this._command("restart");
        }
        finish() {
          this._command("finish");
        }
        destroy() {
          this._command("destroy");
        }
        reset() {
          this._command("reset"), (this._started = !1);
        }
        setPosition(e) {
          this._command("setPosition", e);
        }
        getPosition() {
          var e, t;
          return null !==
            (t =
              null === (e = this._renderer.engine.players[+this.id]) ||
              void 0 === e
                ? void 0
                : e.getPosition()) && void 0 !== t
            ? t
            : 0;
        }
      }
      function PD(n, e, t, i, r) {
        return n.setProperty(e, `@@${t}:${i}`, r);
      }
      const ND = "@.disabled";
      let vV = (() => {
        class n {
          constructor(t, i, r) {
            (this.delegate = t),
              (this.engine = i),
              (this._zone = r),
              (this._currentId = 0),
              (this._microtaskId = 1),
              (this._animationCallbacksBuffer = []),
              (this._rendererCache = new Map()),
              (this._cdRecurDepth = 0),
              (this.promise = Promise.resolve(0)),
              (i.onRemovalComplete = (s, o) => {
                const a = null == o ? void 0 : o.parentNode(s);
                a && o.removeChild(a, s);
              });
          }
          createRenderer(t, i) {
            const s = this.delegate.createRenderer(t, i);
            if (!(t && i && i.data && i.data.animation)) {
              let u = this._rendererCache.get(s);
              return (
                u ||
                  ((u = new LD("", s, this.engine)),
                  this._rendererCache.set(s, u)),
                u
              );
            }
            const o = i.id,
              a = i.id + "-" + this._currentId;
            this._currentId++, this.engine.register(a, t);
            const l = (u) => {
              Array.isArray(u)
                ? u.forEach(l)
                : this.engine.registerTrigger(o, a, t, u.name, u);
            };
            return i.data.animation.forEach(l), new bV(this, a, s, this.engine);
          }
          begin() {
            this._cdRecurDepth++, this.delegate.begin && this.delegate.begin();
          }
          _scheduleCountTask() {
            this.promise.then(() => {
              this._microtaskId++;
            });
          }
          scheduleListenerCallback(t, i, r) {
            t >= 0 && t < this._microtaskId
              ? this._zone.run(() => i(r))
              : (0 == this._animationCallbacksBuffer.length &&
                  Promise.resolve(null).then(() => {
                    this._zone.run(() => {
                      this._animationCallbacksBuffer.forEach((s) => {
                        const [o, a] = s;
                        o(a);
                      }),
                        (this._animationCallbacksBuffer = []);
                    });
                  }),
                this._animationCallbacksBuffer.push([i, r]));
          }
          end() {
            this._cdRecurDepth--,
              0 == this._cdRecurDepth &&
                this._zone.runOutsideAngular(() => {
                  this._scheduleCountTask(),
                    this.engine.flush(this._microtaskId);
                }),
              this.delegate.end && this.delegate.end();
          }
          whenRenderingDone() {
            return this.engine.whenRenderingDone();
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(ao), b(ic), b(ee));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      class LD {
        constructor(e, t, i) {
          (this.namespaceId = e),
            (this.delegate = t),
            (this.engine = i),
            (this.destroyNode = this.delegate.destroyNode
              ? (r) => t.destroyNode(r)
              : null);
        }
        get data() {
          return this.delegate.data;
        }
        destroy() {
          this.engine.destroy(this.namespaceId, this.delegate),
            this.delegate.destroy();
        }
        createElement(e, t) {
          return this.delegate.createElement(e, t);
        }
        createComment(e) {
          return this.delegate.createComment(e);
        }
        createText(e) {
          return this.delegate.createText(e);
        }
        appendChild(e, t) {
          this.delegate.appendChild(e, t),
            this.engine.onInsert(this.namespaceId, t, e, !1);
        }
        insertBefore(e, t, i, r = !0) {
          this.delegate.insertBefore(e, t, i),
            this.engine.onInsert(this.namespaceId, t, e, r);
        }
        removeChild(e, t, i) {
          this.engine.onRemove(this.namespaceId, t, this.delegate, i);
        }
        selectRootElement(e, t) {
          return this.delegate.selectRootElement(e, t);
        }
        parentNode(e) {
          return this.delegate.parentNode(e);
        }
        nextSibling(e) {
          return this.delegate.nextSibling(e);
        }
        setAttribute(e, t, i, r) {
          this.delegate.setAttribute(e, t, i, r);
        }
        removeAttribute(e, t, i) {
          this.delegate.removeAttribute(e, t, i);
        }
        addClass(e, t) {
          this.delegate.addClass(e, t);
        }
        removeClass(e, t) {
          this.delegate.removeClass(e, t);
        }
        setStyle(e, t, i, r) {
          this.delegate.setStyle(e, t, i, r);
        }
        removeStyle(e, t, i) {
          this.delegate.removeStyle(e, t, i);
        }
        setProperty(e, t, i) {
          "@" == t.charAt(0) && t == ND
            ? this.disableAnimations(e, !!i)
            : this.delegate.setProperty(e, t, i);
        }
        setValue(e, t) {
          this.delegate.setValue(e, t);
        }
        listen(e, t, i) {
          return this.delegate.listen(e, t, i);
        }
        disableAnimations(e, t) {
          this.engine.disableAnimations(e, t);
        }
      }
      class bV extends LD {
        constructor(e, t, i, r) {
          super(t, i, r), (this.factory = e), (this.namespaceId = t);
        }
        setProperty(e, t, i) {
          "@" == t.charAt(0)
            ? "." == t.charAt(1) && t == ND
              ? this.disableAnimations(e, (i = void 0 === i || !!i))
              : this.engine.process(this.namespaceId, e, t.substr(1), i)
            : this.delegate.setProperty(e, t, i);
        }
        listen(e, t, i) {
          if ("@" == t.charAt(0)) {
            const r = (function CV(n) {
              switch (n) {
                case "body":
                  return document.body;
                case "document":
                  return document;
                case "window":
                  return window;
                default:
                  return n;
              }
            })(e);
            let s = t.substr(1),
              o = "";
            return (
              "@" != s.charAt(0) &&
                ([s, o] = (function wV(n) {
                  const e = n.indexOf(".");
                  return [n.substring(0, e), n.substr(e + 1)];
                })(s)),
              this.engine.listen(this.namespaceId, r, s, o, (a) => {
                this.factory.scheduleListenerCallback(a._data || -1, i, a);
              })
            );
          }
          return this.delegate.listen(e, t, i);
        }
      }
      let DV = (() => {
        class n extends ic {
          constructor(t, i, r) {
            super(t.body, i, r);
          }
          ngOnDestroy() {
            this.flush();
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(ue), b(Df), b(Pf));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      const No = new T("AnimationModuleType"),
        VD = [
          { provide: zw, useClass: mV },
          {
            provide: Pf,
            useFactory: function MV() {
              return new OL();
            },
          },
          { provide: ic, useClass: DV },
          {
            provide: ao,
            useFactory: function SV(n, e, t) {
              return new vV(n, e, t);
            },
            deps: [Ml, ic, ee],
          },
        ],
        BD = [
          {
            provide: Df,
            useFactory: function EV() {
              return (function gV() {
                return "function" == typeof RD();
              })()
                ? new pV()
                : new xD();
            },
          },
          { provide: No, useValue: "BrowserAnimations" },
          ...VD,
        ],
        AV = [
          { provide: Df, useClass: eD },
          { provide: No, useValue: "NoopAnimations" },
          ...VD,
        ];
      let TV = (() => {
        class n {
          static withConfig(t) {
            return { ngModule: n, providers: t.disableAnimations ? AV : BD };
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵmod = he({ type: n })),
          (n.ɵinj = ce({ providers: BD, imports: [gC] })),
          n
        );
      })();
      function OV(n, e) {
        if ((1 & n && Me(0, "mat-pseudo-checkbox", 4), 2 & n)) {
          const t = K();
          F("state", t.selected ? "checked" : "unchecked")(
            "disabled",
            t.disabled
          );
        }
      }
      function IV(n, e) {
        if ((1 & n && (D(0, "span", 5), J(1), E()), 2 & n)) {
          const t = K();
          k(1), no("(", t.group.label, ")");
        }
      }
      const xV = ["*"],
        FV = new T("mat-sanity-checks", {
          providedIn: "root",
          factory: function kV() {
            return !0;
          },
        });
      let bn = (() => {
        class n {
          constructor(t, i, r) {
            (this._sanityChecks = i),
              (this._document = r),
              (this._hasDoneGlobalChecks = !1),
              t._applyBodyHighContrastModeCssClasses(),
              this._hasDoneGlobalChecks || (this._hasDoneGlobalChecks = !0);
          }
          _checkIsEnabled(t) {
            return (
              !nf() &&
              ("boolean" == typeof this._sanityChecks
                ? this._sanityChecks
                : !!this._sanityChecks[t])
            );
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(JN), b(FV, 8), b(ue));
          }),
          (n.ɵmod = he({ type: n })),
          (n.ɵinj = ce({ imports: [[Io], Io] })),
          n
        );
      })();
      function RV(n) {
        return class extends n {
          constructor(...e) {
            super(...e), (this._disabled = !1);
          }
          get disabled() {
            return this._disabled;
          }
          set disabled(e) {
            this._disabled = je(e);
          }
        };
      }
      function PV(n, e) {
        return class extends n {
          constructor(...t) {
            super(...t), (this.defaultColor = e), (this.color = e);
          }
          get color() {
            return this._color;
          }
          set color(t) {
            const i = t || this.defaultColor;
            i !== this._color &&
              (this._color &&
                this._elementRef.nativeElement.classList.remove(
                  `mat-${this._color}`
                ),
              i && this._elementRef.nativeElement.classList.add(`mat-${i}`),
              (this._color = i));
          }
        };
      }
      function HD(n) {
        return class extends n {
          constructor(...e) {
            super(...e), (this._disableRipple = !1);
          }
          get disableRipple() {
            return this._disableRipple;
          }
          set disableRipple(e) {
            this._disableRipple = je(e);
          }
        };
      }
      function NV(n, e = 0) {
        return class extends n {
          constructor(...t) {
            super(...t), (this._tabIndex = e), (this.defaultTabIndex = e);
          }
          get tabIndex() {
            return this.disabled ? -1 : this._tabIndex;
          }
          set tabIndex(t) {
            this._tabIndex = null != t ? Oh(t) : this.defaultTabIndex;
          }
        };
      }
      function UD(n) {
        return class extends n {
          constructor(...e) {
            super(...e), (this.stateChanges = new le()), (this.errorState = !1);
          }
          updateErrorState() {
            const e = this.errorState,
              s = (
                this.errorStateMatcher || this._defaultErrorStateMatcher
              ).isErrorState(
                this.ngControl ? this.ngControl.control : null,
                this._parentFormGroup || this._parentForm
              );
            s !== e && ((this.errorState = s), this.stateChanges.next());
          }
        };
      }
      let zf = (() => {
        class n {
          isErrorState(t, i) {
            return !!(t && t.invalid && (t.touched || (i && i.submitted)));
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
          n
        );
      })();
      class VV {
        constructor(e, t, i) {
          (this._renderer = e),
            (this.element = t),
            (this.config = i),
            (this.state = 3);
        }
        fadeOut() {
          this._renderer.fadeOutRipple(this);
        }
      }
      const $D = { enterDuration: 225, exitDuration: 150 },
        Gf = Ll({ passive: !0 }),
        zD = ["mousedown", "touchstart"],
        GD = ["mouseup", "mouseleave", "touchend", "touchcancel"];
      class jV {
        constructor(e, t, i, r) {
          (this._target = e),
            (this._ngZone = t),
            (this._isPointerDown = !1),
            (this._activeRipples = new Set()),
            (this._pointerUpEventsRegistered = !1),
            r.isBrowser && (this._containerElement = ei(i));
        }
        fadeInRipple(e, t, i = {}) {
          const r = (this._containerRect =
              this._containerRect ||
              this._containerElement.getBoundingClientRect()),
            s = Object.assign(Object.assign({}, $D), i.animation);
          i.centered &&
            ((e = r.left + r.width / 2), (t = r.top + r.height / 2));
          const o =
              i.radius ||
              (function UV(n, e, t) {
                const i = Math.max(Math.abs(n - t.left), Math.abs(n - t.right)),
                  r = Math.max(Math.abs(e - t.top), Math.abs(e - t.bottom));
                return Math.sqrt(i * i + r * r);
              })(e, t, r),
            a = e - r.left,
            l = t - r.top,
            c = s.enterDuration,
            u = document.createElement("div");
          u.classList.add("mat-ripple-element"),
            (u.style.left = a - o + "px"),
            (u.style.top = l - o + "px"),
            (u.style.height = 2 * o + "px"),
            (u.style.width = 2 * o + "px"),
            null != i.color && (u.style.backgroundColor = i.color),
            (u.style.transitionDuration = `${c}ms`),
            this._containerElement.appendChild(u),
            (function HV(n) {
              window.getComputedStyle(n).getPropertyValue("opacity");
            })(u),
            (u.style.transform = "scale(1)");
          const d = new VV(this, u, i);
          return (
            (d.state = 0),
            this._activeRipples.add(d),
            i.persistent || (this._mostRecentTransientRipple = d),
            this._runTimeoutOutsideZone(() => {
              const h = d === this._mostRecentTransientRipple;
              (d.state = 1),
                !i.persistent && (!h || !this._isPointerDown) && d.fadeOut();
            }, c),
            d
          );
        }
        fadeOutRipple(e) {
          const t = this._activeRipples.delete(e);
          if (
            (e === this._mostRecentTransientRipple &&
              (this._mostRecentTransientRipple = null),
            this._activeRipples.size || (this._containerRect = null),
            !t)
          )
            return;
          const i = e.element,
            r = Object.assign(Object.assign({}, $D), e.config.animation);
          (i.style.transitionDuration = `${r.exitDuration}ms`),
            (i.style.opacity = "0"),
            (e.state = 2),
            this._runTimeoutOutsideZone(() => {
              (e.state = 3), i.remove();
            }, r.exitDuration);
        }
        fadeOutAll() {
          this._activeRipples.forEach((e) => e.fadeOut());
        }
        fadeOutAllNonPersistent() {
          this._activeRipples.forEach((e) => {
            e.config.persistent || e.fadeOut();
          });
        }
        setupTriggerEvents(e) {
          const t = ei(e);
          !t ||
            t === this._triggerElement ||
            (this._removeTriggerEvents(),
            (this._triggerElement = t),
            this._registerEvents(zD));
        }
        handleEvent(e) {
          "mousedown" === e.type
            ? this._onMousedown(e)
            : "touchstart" === e.type
            ? this._onTouchStart(e)
            : this._onPointerUp(),
            this._pointerUpEventsRegistered ||
              (this._registerEvents(GD),
              (this._pointerUpEventsRegistered = !0));
        }
        _onMousedown(e) {
          const t = Bw(e),
            i =
              this._lastTouchStartEvent &&
              Date.now() < this._lastTouchStartEvent + 800;
          !this._target.rippleDisabled &&
            !t &&
            !i &&
            ((this._isPointerDown = !0),
            this.fadeInRipple(e.clientX, e.clientY, this._target.rippleConfig));
        }
        _onTouchStart(e) {
          if (!this._target.rippleDisabled && !jw(e)) {
            (this._lastTouchStartEvent = Date.now()),
              (this._isPointerDown = !0);
            const t = e.changedTouches;
            for (let i = 0; i < t.length; i++)
              this.fadeInRipple(
                t[i].clientX,
                t[i].clientY,
                this._target.rippleConfig
              );
          }
        }
        _onPointerUp() {
          !this._isPointerDown ||
            ((this._isPointerDown = !1),
            this._activeRipples.forEach((e) => {
              !e.config.persistent &&
                (1 === e.state ||
                  (e.config.terminateOnPointerUp && 0 === e.state)) &&
                e.fadeOut();
            }));
        }
        _runTimeoutOutsideZone(e, t = 0) {
          this._ngZone.runOutsideAngular(() => setTimeout(e, t));
        }
        _registerEvents(e) {
          this._ngZone.runOutsideAngular(() => {
            e.forEach((t) => {
              this._triggerElement.addEventListener(t, this, Gf);
            });
          });
        }
        _removeTriggerEvents() {
          this._triggerElement &&
            (zD.forEach((e) => {
              this._triggerElement.removeEventListener(e, this, Gf);
            }),
            this._pointerUpEventsRegistered &&
              GD.forEach((e) => {
                this._triggerElement.removeEventListener(e, this, Gf);
              }));
        }
      }
      const $V = new T("mat-ripple-global-options");
      let qD = (() => {
          class n {
            constructor(t, i, r, s, o) {
              (this._elementRef = t),
                (this._animationMode = o),
                (this.radius = 0),
                (this._disabled = !1),
                (this._isInitialized = !1),
                (this._globalOptions = s || {}),
                (this._rippleRenderer = new jV(this, i, t, r));
            }
            get disabled() {
              return this._disabled;
            }
            set disabled(t) {
              t && this.fadeOutAllNonPersistent(),
                (this._disabled = t),
                this._setupTriggerEventsIfEnabled();
            }
            get trigger() {
              return this._trigger || this._elementRef.nativeElement;
            }
            set trigger(t) {
              (this._trigger = t), this._setupTriggerEventsIfEnabled();
            }
            ngOnInit() {
              (this._isInitialized = !0), this._setupTriggerEventsIfEnabled();
            }
            ngOnDestroy() {
              this._rippleRenderer._removeTriggerEvents();
            }
            fadeOutAll() {
              this._rippleRenderer.fadeOutAll();
            }
            fadeOutAllNonPersistent() {
              this._rippleRenderer.fadeOutAllNonPersistent();
            }
            get rippleConfig() {
              return {
                centered: this.centered,
                radius: this.radius,
                color: this.color,
                animation: Object.assign(
                  Object.assign(
                    Object.assign({}, this._globalOptions.animation),
                    "NoopAnimations" === this._animationMode
                      ? { enterDuration: 0, exitDuration: 0 }
                      : {}
                  ),
                  this.animation
                ),
                terminateOnPointerUp: this._globalOptions.terminateOnPointerUp,
              };
            }
            get rippleDisabled() {
              return this.disabled || !!this._globalOptions.disabled;
            }
            _setupTriggerEventsIfEnabled() {
              !this.disabled &&
                this._isInitialized &&
                this._rippleRenderer.setupTriggerEvents(this.trigger);
            }
            launch(t, i = 0, r) {
              return "number" == typeof t
                ? this._rippleRenderer.fadeInRipple(
                    t,
                    i,
                    Object.assign(Object.assign({}, this.rippleConfig), r)
                  )
                : this._rippleRenderer.fadeInRipple(
                    0,
                    0,
                    Object.assign(Object.assign({}, this.rippleConfig), t)
                  );
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(Se), _(ee), _(Jt), _($V, 8), _(No, 8));
            }),
            (n.ɵdir = x({
              type: n,
              selectors: [
                ["", "mat-ripple", ""],
                ["", "matRipple", ""],
              ],
              hostAttrs: [1, "mat-ripple"],
              hostVars: 2,
              hostBindings: function (t, i) {
                2 & t && Dt("mat-ripple-unbounded", i.unbounded);
              },
              inputs: {
                color: ["matRippleColor", "color"],
                unbounded: ["matRippleUnbounded", "unbounded"],
                centered: ["matRippleCentered", "centered"],
                radius: ["matRippleRadius", "radius"],
                animation: ["matRippleAnimation", "animation"],
                disabled: ["matRippleDisabled", "disabled"],
                trigger: ["matRippleTrigger", "trigger"],
              },
              exportAs: ["matRipple"],
            })),
            n
          );
        })(),
        WD = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({ imports: [[bn], bn] })),
            n
          );
        })(),
        zV = (() => {
          class n {
            constructor(t) {
              (this._animationMode = t),
                (this.state = "unchecked"),
                (this.disabled = !1);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(No, 8));
            }),
            (n.ɵcmp = Dn({
              type: n,
              selectors: [["mat-pseudo-checkbox"]],
              hostAttrs: [1, "mat-pseudo-checkbox"],
              hostVars: 8,
              hostBindings: function (t, i) {
                2 & t &&
                  Dt(
                    "mat-pseudo-checkbox-indeterminate",
                    "indeterminate" === i.state
                  )("mat-pseudo-checkbox-checked", "checked" === i.state)(
                    "mat-pseudo-checkbox-disabled",
                    i.disabled
                  )(
                    "_mat-animation-noopable",
                    "NoopAnimations" === i._animationMode
                  );
              },
              inputs: { state: "state", disabled: "disabled" },
              decls: 0,
              vars: 0,
              template: function (t, i) {},
              styles: [
                '.mat-pseudo-checkbox{width:16px;height:16px;border:2px solid;border-radius:2px;cursor:pointer;display:inline-block;vertical-align:middle;box-sizing:border-box;position:relative;flex-shrink:0;transition:border-color 90ms cubic-bezier(0, 0, 0.2, 0.1),background-color 90ms cubic-bezier(0, 0, 0.2, 0.1)}.mat-pseudo-checkbox::after{position:absolute;opacity:0;content:"";border-bottom:2px solid currentColor;transition:opacity 90ms cubic-bezier(0, 0, 0.2, 0.1)}.mat-pseudo-checkbox.mat-pseudo-checkbox-checked,.mat-pseudo-checkbox.mat-pseudo-checkbox-indeterminate{border-color:transparent}._mat-animation-noopable.mat-pseudo-checkbox{transition:none;animation:none}._mat-animation-noopable.mat-pseudo-checkbox::after{transition:none}.mat-pseudo-checkbox-disabled{cursor:default}.mat-pseudo-checkbox-indeterminate::after{top:5px;left:1px;width:10px;opacity:1;border-radius:2px}.mat-pseudo-checkbox-checked::after{top:2.4px;left:1px;width:8px;height:3px;border-left:2px solid currentColor;transform:rotate(-45deg);opacity:1;box-sizing:content-box}\n',
              ],
              encapsulation: 2,
              changeDetection: 0,
            })),
            n
          );
        })(),
        GV = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({ imports: [[bn]] })),
            n
          );
        })();
      const KD = new T("MAT_OPTION_PARENT_COMPONENT"),
        YD = new T("MatOptgroup");
      let qV = 0;
      class WV {
        constructor(e, t = !1) {
          (this.source = e), (this.isUserInput = t);
        }
      }
      let KV = (() => {
          class n {
            constructor(t, i, r, s) {
              (this._element = t),
                (this._changeDetectorRef = i),
                (this._parent = r),
                (this.group = s),
                (this._selected = !1),
                (this._active = !1),
                (this._disabled = !1),
                (this._mostRecentViewValue = ""),
                (this.id = "mat-option-" + qV++),
                (this.onSelectionChange = new Q()),
                (this._stateChanges = new le());
            }
            get multiple() {
              return this._parent && this._parent.multiple;
            }
            get selected() {
              return this._selected;
            }
            get disabled() {
              return (this.group && this.group.disabled) || this._disabled;
            }
            set disabled(t) {
              this._disabled = je(t);
            }
            get disableRipple() {
              return !(!this._parent || !this._parent.disableRipple);
            }
            get active() {
              return this._active;
            }
            get viewValue() {
              return (this._getHostElement().textContent || "").trim();
            }
            select() {
              this._selected ||
                ((this._selected = !0),
                this._changeDetectorRef.markForCheck(),
                this._emitSelectionChangeEvent());
            }
            deselect() {
              this._selected &&
                ((this._selected = !1),
                this._changeDetectorRef.markForCheck(),
                this._emitSelectionChangeEvent());
            }
            focus(t, i) {
              const r = this._getHostElement();
              "function" == typeof r.focus && r.focus(i);
            }
            setActiveStyles() {
              this._active ||
                ((this._active = !0), this._changeDetectorRef.markForCheck());
            }
            setInactiveStyles() {
              this._active &&
                ((this._active = !1), this._changeDetectorRef.markForCheck());
            }
            getLabel() {
              return this.viewValue;
            }
            _handleKeydown(t) {
              (13 === t.keyCode || 32 === t.keyCode) &&
                !ko(t) &&
                (this._selectViaInteraction(), t.preventDefault());
            }
            _selectViaInteraction() {
              this.disabled ||
                ((this._selected = !this.multiple || !this._selected),
                this._changeDetectorRef.markForCheck(),
                this._emitSelectionChangeEvent(!0));
            }
            _getAriaSelected() {
              return this.selected || (!this.multiple && null);
            }
            _getTabIndex() {
              return this.disabled ? "-1" : "0";
            }
            _getHostElement() {
              return this._element.nativeElement;
            }
            ngAfterViewChecked() {
              if (this._selected) {
                const t = this.viewValue;
                t !== this._mostRecentViewValue &&
                  ((this._mostRecentViewValue = t), this._stateChanges.next());
              }
            }
            ngOnDestroy() {
              this._stateChanges.complete();
            }
            _emitSelectionChangeEvent(t = !1) {
              this.onSelectionChange.emit(new WV(this, t));
            }
          }
          return (
            (n.ɵfac = function (t) {
              $a();
            }),
            (n.ɵdir = x({
              type: n,
              inputs: { value: "value", id: "id", disabled: "disabled" },
              outputs: { onSelectionChange: "onSelectionChange" },
            })),
            n
          );
        })(),
        ZD = (() => {
          class n extends KV {
            constructor(t, i, r, s) {
              super(t, i, r, s);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(Se), _(vi), _(KD, 8), _(YD, 8));
            }),
            (n.ɵcmp = Dn({
              type: n,
              selectors: [["mat-option"]],
              hostAttrs: [
                "role",
                "option",
                1,
                "mat-option",
                "mat-focus-indicator",
              ],
              hostVars: 12,
              hostBindings: function (t, i) {
                1 & t &&
                  Z("click", function () {
                    return i._selectViaInteraction();
                  })("keydown", function (s) {
                    return i._handleKeydown(s);
                  }),
                  2 & t &&
                    (Wa("id", i.id),
                    $e("tabindex", i._getTabIndex())(
                      "aria-selected",
                      i._getAriaSelected()
                    )("aria-disabled", i.disabled.toString()),
                    Dt("mat-selected", i.selected)(
                      "mat-option-multiple",
                      i.multiple
                    )("mat-active", i.active)(
                      "mat-option-disabled",
                      i.disabled
                    ));
              },
              exportAs: ["matOption"],
              features: [se],
              ngContentSelectors: xV,
              decls: 5,
              vars: 4,
              consts: [
                [
                  "class",
                  "mat-option-pseudo-checkbox",
                  3,
                  "state",
                  "disabled",
                  4,
                  "ngIf",
                ],
                [1, "mat-option-text"],
                ["class", "cdk-visually-hidden", 4, "ngIf"],
                [
                  "mat-ripple",
                  "",
                  1,
                  "mat-option-ripple",
                  3,
                  "matRippleTrigger",
                  "matRippleDisabled",
                ],
                [1, "mat-option-pseudo-checkbox", 3, "state", "disabled"],
                [1, "cdk-visually-hidden"],
              ],
              template: function (t, i) {
                1 & t &&
                  (eo(),
                  be(0, OV, 1, 2, "mat-pseudo-checkbox", 0),
                  D(1, "span", 1),
                  Rt(2),
                  E(),
                  be(3, IV, 2, 1, "span", 2),
                  Me(4, "div", 3)),
                  2 & t &&
                    (F("ngIf", i.multiple),
                    k(3),
                    F("ngIf", i.group && i.group._inert),
                    k(1),
                    F("matRippleTrigger", i._getHostElement())(
                      "matRippleDisabled",
                      i.disabled || i.disableRipple
                    ));
              },
              directives: [zV, vl, qD],
              styles: [
                ".mat-option{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block;line-height:48px;height:48px;padding:0 16px;text-align:left;text-decoration:none;max-width:100%;position:relative;cursor:pointer;outline:none;display:flex;flex-direction:row;max-width:100%;box-sizing:border-box;align-items:center;-webkit-tap-highlight-color:transparent}.mat-option[disabled]{cursor:default}[dir=rtl] .mat-option{text-align:right}.mat-option .mat-icon{margin-right:16px;vertical-align:middle}.mat-option .mat-icon svg{vertical-align:top}[dir=rtl] .mat-option .mat-icon{margin-left:16px;margin-right:0}.mat-option[aria-disabled=true]{-webkit-user-select:none;user-select:none;cursor:default}.mat-optgroup .mat-option:not(.mat-option-multiple){padding-left:32px}[dir=rtl] .mat-optgroup .mat-option:not(.mat-option-multiple){padding-left:16px;padding-right:32px}.cdk-high-contrast-active .mat-option{margin:0 1px}.cdk-high-contrast-active .mat-option.mat-active{border:solid 1px currentColor;margin:0}.cdk-high-contrast-active .mat-option[aria-disabled=true]{opacity:.5}.mat-option-text{display:inline-block;flex-grow:1;overflow:hidden;text-overflow:ellipsis}.mat-option .mat-option-ripple{top:0;left:0;right:0;bottom:0;position:absolute;pointer-events:none}.mat-option-pseudo-checkbox{margin-right:8px}[dir=rtl] .mat-option-pseudo-checkbox{margin-left:8px;margin-right:0}\n",
              ],
              encapsulation: 2,
              changeDetection: 0,
            })),
            n
          );
        })();
      function QD(n, e, t) {
        if (t.length) {
          let i = e.toArray(),
            r = t.toArray(),
            s = 0;
          for (let o = 0; o < n + 1; o++)
            i[o].group && i[o].group === r[s] && s++;
          return s;
        }
        return 0;
      }
      let XD = (() => {
        class n {}
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵmod = he({ type: n })),
          (n.ɵinj = ce({ imports: [[WD, bl, bn, GV]] })),
          n
        );
      })();
      const ZV = ["button"],
        QV = ["*"],
        JD = new T("MAT_BUTTON_TOGGLE_DEFAULT_OPTIONS"),
        eE = new T("MatButtonToggleGroup"),
        XV = { provide: vn, useExisting: _e(() => iE), multi: !0 };
      let tE = 0;
      class nE {
        constructor(e, t) {
          (this.source = e), (this.value = t);
        }
      }
      let iE = (() => {
        class n {
          constructor(t, i) {
            (this._changeDetector = t),
              (this._vertical = !1),
              (this._multiple = !1),
              (this._disabled = !1),
              (this._controlValueAccessorChangeFn = () => {}),
              (this._onTouched = () => {}),
              (this._name = "mat-button-toggle-group-" + tE++),
              (this.valueChange = new Q()),
              (this.change = new Q()),
              (this.appearance = i && i.appearance ? i.appearance : "standard");
          }
          get name() {
            return this._name;
          }
          set name(t) {
            (this._name = t),
              this._buttonToggles &&
                this._buttonToggles.forEach((i) => {
                  (i.name = this._name), i._markForCheck();
                });
          }
          get vertical() {
            return this._vertical;
          }
          set vertical(t) {
            this._vertical = je(t);
          }
          get value() {
            const t = this._selectionModel ? this._selectionModel.selected : [];
            return this.multiple
              ? t.map((i) => i.value)
              : t[0]
              ? t[0].value
              : void 0;
          }
          set value(t) {
            this._setSelectionByValue(t), this.valueChange.emit(this.value);
          }
          get selected() {
            const t = this._selectionModel ? this._selectionModel.selected : [];
            return this.multiple ? t : t[0] || null;
          }
          get multiple() {
            return this._multiple;
          }
          set multiple(t) {
            this._multiple = je(t);
          }
          get disabled() {
            return this._disabled;
          }
          set disabled(t) {
            (this._disabled = je(t)),
              this._buttonToggles &&
                this._buttonToggles.forEach((i) => i._markForCheck());
          }
          ngOnInit() {
            this._selectionModel = new vC(this.multiple, void 0, !1);
          }
          ngAfterContentInit() {
            this._selectionModel.select(
              ...this._buttonToggles.filter((t) => t.checked)
            );
          }
          writeValue(t) {
            (this.value = t), this._changeDetector.markForCheck();
          }
          registerOnChange(t) {
            this._controlValueAccessorChangeFn = t;
          }
          registerOnTouched(t) {
            this._onTouched = t;
          }
          setDisabledState(t) {
            this.disabled = t;
          }
          _emitChangeEvent() {
            const t = this.selected,
              i = Array.isArray(t) ? t[t.length - 1] : t,
              r = new nE(i, this.value);
            this._controlValueAccessorChangeFn(r.value), this.change.emit(r);
          }
          _syncButtonToggle(t, i, r = !1, s = !1) {
            !this.multiple &&
              this.selected &&
              !t.checked &&
              (this.selected.checked = !1),
              this._selectionModel
                ? i
                  ? this._selectionModel.select(t)
                  : this._selectionModel.deselect(t)
                : (s = !0),
              s
                ? Promise.resolve().then(() => this._updateModelValue(r))
                : this._updateModelValue(r);
          }
          _isSelected(t) {
            return this._selectionModel && this._selectionModel.isSelected(t);
          }
          _isPrechecked(t) {
            return (
              void 0 !== this._rawValue &&
              (this.multiple && Array.isArray(this._rawValue)
                ? this._rawValue.some((i) => null != t.value && i === t.value)
                : t.value === this._rawValue)
            );
          }
          _setSelectionByValue(t) {
            (this._rawValue = t),
              this._buttonToggles &&
                (this.multiple && t
                  ? (Array.isArray(t),
                    this._clearSelection(),
                    t.forEach((i) => this._selectValue(i)))
                  : (this._clearSelection(), this._selectValue(t)));
          }
          _clearSelection() {
            this._selectionModel.clear(),
              this._buttonToggles.forEach((t) => (t.checked = !1));
          }
          _selectValue(t) {
            const i = this._buttonToggles.find(
              (r) => null != r.value && r.value === t
            );
            i && ((i.checked = !0), this._selectionModel.select(i));
          }
          _updateModelValue(t) {
            t && this._emitChangeEvent(), this.valueChange.emit(this.value);
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(_(vi), _(JD, 8));
          }),
          (n.ɵdir = x({
            type: n,
            selectors: [["mat-button-toggle-group"]],
            contentQueries: function (t, i, r) {
              if ((1 & t && ut(r, rE, 5), 2 & t)) {
                let s;
                Te((s = Oe())) && (i._buttonToggles = s);
              }
            },
            hostAttrs: ["role", "group", 1, "mat-button-toggle-group"],
            hostVars: 5,
            hostBindings: function (t, i) {
              2 & t &&
                ($e("aria-disabled", i.disabled),
                Dt("mat-button-toggle-vertical", i.vertical)(
                  "mat-button-toggle-group-appearance-standard",
                  "standard" === i.appearance
                ));
            },
            inputs: {
              appearance: "appearance",
              name: "name",
              vertical: "vertical",
              value: "value",
              multiple: "multiple",
              disabled: "disabled",
            },
            outputs: { valueChange: "valueChange", change: "change" },
            exportAs: ["matButtonToggleGroup"],
            features: [ge([XV, { provide: eE, useExisting: n }])],
          })),
          n
        );
      })();
      const JV = HD(class {});
      let rE = (() => {
          class n extends JV {
            constructor(t, i, r, s, o, a) {
              super(),
                (this._changeDetectorRef = i),
                (this._elementRef = r),
                (this._focusMonitor = s),
                (this._isSingleSelector = !1),
                (this._checked = !1),
                (this.ariaLabelledby = null),
                (this._disabled = !1),
                (this.change = new Q());
              const l = Number(o);
              (this.tabIndex = l || 0 === l ? l : null),
                (this.buttonToggleGroup = t),
                (this.appearance =
                  a && a.appearance ? a.appearance : "standard");
            }
            get buttonId() {
              return `${this.id}-button`;
            }
            get appearance() {
              return this.buttonToggleGroup
                ? this.buttonToggleGroup.appearance
                : this._appearance;
            }
            set appearance(t) {
              this._appearance = t;
            }
            get checked() {
              return this.buttonToggleGroup
                ? this.buttonToggleGroup._isSelected(this)
                : this._checked;
            }
            set checked(t) {
              const i = je(t);
              i !== this._checked &&
                ((this._checked = i),
                this.buttonToggleGroup &&
                  this.buttonToggleGroup._syncButtonToggle(this, this._checked),
                this._changeDetectorRef.markForCheck());
            }
            get disabled() {
              return (
                this._disabled ||
                (this.buttonToggleGroup && this.buttonToggleGroup.disabled)
              );
            }
            set disabled(t) {
              this._disabled = je(t);
            }
            ngOnInit() {
              const t = this.buttonToggleGroup;
              (this._isSingleSelector = t && !t.multiple),
                (this.id = this.id || "mat-button-toggle-" + tE++),
                this._isSingleSelector && (this.name = t.name),
                t &&
                  (t._isPrechecked(this)
                    ? (this.checked = !0)
                    : t._isSelected(this) !== this._checked &&
                      t._syncButtonToggle(this, this._checked));
            }
            ngAfterViewInit() {
              this._focusMonitor.monitor(this._elementRef, !0);
            }
            ngOnDestroy() {
              const t = this.buttonToggleGroup;
              this._focusMonitor.stopMonitoring(this._elementRef),
                t &&
                  t._isSelected(this) &&
                  t._syncButtonToggle(this, !1, !1, !0);
            }
            focus(t) {
              this._buttonElement.nativeElement.focus(t);
            }
            _onButtonClick() {
              const t = !!this._isSingleSelector || !this._checked;
              t !== this._checked &&
                ((this._checked = t),
                this.buttonToggleGroup &&
                  (this.buttonToggleGroup._syncButtonToggle(
                    this,
                    this._checked,
                    !0
                  ),
                  this.buttonToggleGroup._onTouched())),
                this.change.emit(new nE(this, this.value));
            }
            _markForCheck() {
              this._changeDetectorRef.markForCheck();
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(
                _(eE, 8),
                _(vi),
                _(Se),
                _(XN),
                Bi("tabindex"),
                _(JD, 8)
              );
            }),
            (n.ɵcmp = Dn({
              type: n,
              selectors: [["mat-button-toggle"]],
              viewQuery: function (t, i) {
                if ((1 & t && yi(ZV, 5), 2 & t)) {
                  let r;
                  Te((r = Oe())) && (i._buttonElement = r.first);
                }
              },
              hostAttrs: ["role", "presentation", 1, "mat-button-toggle"],
              hostVars: 12,
              hostBindings: function (t, i) {
                1 & t &&
                  Z("focus", function () {
                    return i.focus();
                  }),
                  2 & t &&
                    ($e("aria-label", null)("aria-labelledby", null)(
                      "id",
                      i.id
                    )("name", null),
                    Dt("mat-button-toggle-standalone", !i.buttonToggleGroup)(
                      "mat-button-toggle-checked",
                      i.checked
                    )("mat-button-toggle-disabled", i.disabled)(
                      "mat-button-toggle-appearance-standard",
                      "standard" === i.appearance
                    ));
              },
              inputs: {
                disableRipple: "disableRipple",
                ariaLabel: ["aria-label", "ariaLabel"],
                ariaLabelledby: ["aria-labelledby", "ariaLabelledby"],
                id: "id",
                name: "name",
                value: "value",
                tabIndex: "tabIndex",
                appearance: "appearance",
                checked: "checked",
                disabled: "disabled",
              },
              outputs: { change: "change" },
              exportAs: ["matButtonToggle"],
              features: [se],
              ngContentSelectors: QV,
              decls: 6,
              vars: 9,
              consts: [
                [
                  "type",
                  "button",
                  1,
                  "mat-button-toggle-button",
                  "mat-focus-indicator",
                  3,
                  "id",
                  "disabled",
                  "click",
                ],
                ["button", ""],
                [1, "mat-button-toggle-label-content"],
                [1, "mat-button-toggle-focus-overlay"],
                [
                  "matRipple",
                  "",
                  1,
                  "mat-button-toggle-ripple",
                  3,
                  "matRippleTrigger",
                  "matRippleDisabled",
                ],
              ],
              template: function (t, i) {
                if (
                  (1 & t &&
                    (eo(),
                    D(0, "button", 0, 1),
                    Z("click", function () {
                      return i._onButtonClick();
                    }),
                    D(2, "span", 2),
                    Rt(3),
                    E(),
                    E(),
                    Me(4, "span", 3),
                    Me(5, "span", 4)),
                  2 & t)
                ) {
                  const r = bd(1);
                  F("id", i.buttonId)("disabled", i.disabled || null),
                    $e("tabindex", i.disabled ? -1 : i.tabIndex)(
                      "aria-pressed",
                      i.checked
                    )("name", i.name || null)("aria-label", i.ariaLabel)(
                      "aria-labelledby",
                      i.ariaLabelledby
                    ),
                    k(5),
                    F("matRippleTrigger", r)(
                      "matRippleDisabled",
                      i.disableRipple || i.disabled
                    );
                }
              },
              directives: [qD],
              styles: [
                ".mat-button-toggle-standalone,.mat-button-toggle-group{position:relative;display:inline-flex;flex-direction:row;white-space:nowrap;overflow:hidden;border-radius:2px;-webkit-tap-highlight-color:transparent;transform:translateZ(0)}.cdk-high-contrast-active .mat-button-toggle-standalone,.cdk-high-contrast-active .mat-button-toggle-group{outline:solid 1px}.mat-button-toggle-standalone.mat-button-toggle-appearance-standard,.mat-button-toggle-group-appearance-standard{border-radius:4px}.cdk-high-contrast-active .mat-button-toggle-standalone.mat-button-toggle-appearance-standard,.cdk-high-contrast-active .mat-button-toggle-group-appearance-standard{outline:0}.mat-button-toggle-vertical{flex-direction:column}.mat-button-toggle-vertical .mat-button-toggle-label-content{display:block}.mat-button-toggle{white-space:nowrap;position:relative}.mat-button-toggle .mat-icon svg{vertical-align:top}.mat-button-toggle.cdk-keyboard-focused .mat-button-toggle-focus-overlay{opacity:1}.cdk-high-contrast-active .mat-button-toggle.cdk-keyboard-focused .mat-button-toggle-focus-overlay{opacity:.5}.mat-button-toggle-appearance-standard:not(.mat-button-toggle-disabled):hover .mat-button-toggle-focus-overlay{opacity:.04}.mat-button-toggle-appearance-standard.cdk-keyboard-focused:not(.mat-button-toggle-disabled) .mat-button-toggle-focus-overlay{opacity:.12}.cdk-high-contrast-active .mat-button-toggle-appearance-standard.cdk-keyboard-focused:not(.mat-button-toggle-disabled) .mat-button-toggle-focus-overlay{opacity:.5}@media(hover: none){.mat-button-toggle-appearance-standard:not(.mat-button-toggle-disabled):hover .mat-button-toggle-focus-overlay{display:none}}.mat-button-toggle-label-content{-webkit-user-select:none;user-select:none;display:inline-block;line-height:36px;padding:0 16px;position:relative}.mat-button-toggle-appearance-standard .mat-button-toggle-label-content{padding:0 12px}.mat-button-toggle-label-content>*{vertical-align:middle}.mat-button-toggle-focus-overlay{border-radius:inherit;pointer-events:none;opacity:0;top:0;left:0;right:0;bottom:0;position:absolute}.mat-button-toggle-checked .cdk-high-contrast-active .mat-button-toggle-focus-overlay{border-bottom:solid 36px;opacity:.5;height:0}.cdk-high-contrast-active .mat-button-toggle-checked.mat-button-toggle-appearance-standard .mat-button-toggle-focus-overlay{border-bottom:solid 500px}.mat-button-toggle .mat-button-toggle-ripple{top:0;left:0;right:0;bottom:0;position:absolute;pointer-events:none}.mat-button-toggle-button{border:0;background:none;color:inherit;padding:0;margin:0;font:inherit;outline:none;width:100%;cursor:pointer}.mat-button-toggle-disabled .mat-button-toggle-button{cursor:default}.mat-button-toggle-button::-moz-focus-inner{border:0}\n",
              ],
              encapsulation: 2,
              changeDetection: 0,
            })),
            n
          );
        })(),
        eB = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({ imports: [[bn, WD], bn] })),
            n
          );
        })();
      function sE(n, e, t) {
        n ? Hn(t, n, e) : e();
      }
      const oc = Cs(
        (n) =>
          function () {
            n(this),
              (this.name = "EmptyError"),
              (this.message = "no elements in sequence");
          }
      );
      function qf(...n) {
        return (function iB() {
          return Ds(1);
        })()(et(n, Es(n)));
      }
      function Wf(n) {
        return new fe((e) => {
          St(n()).subscribe(e);
        });
      }
      function oE() {
        return Fe((n, e) => {
          let t = null;
          n._refCount++;
          const i = new De(e, void 0, void 0, void 0, () => {
            if (!n || n._refCount <= 0 || 0 < --n._refCount)
              return void (t = null);
            const r = n._connection,
              s = t;
            (t = null),
              r && (!s || r === s) && r.unsubscribe(),
              e.unsubscribe();
          });
          n.subscribe(i), i.closed || (t = n.connect());
        });
      }
      class rB extends fe {
        constructor(e, t) {
          super(),
            (this.source = e),
            (this.subjectFactory = t),
            (this._subject = null),
            (this._refCount = 0),
            (this._connection = null),
            Vp(e) && (this.lift = e.lift);
        }
        _subscribe(e) {
          return this.getSubject().subscribe(e);
        }
        getSubject() {
          const e = this._subject;
          return (
            (!e || e.isStopped) && (this._subject = this.subjectFactory()),
            this._subject
          );
        }
        _teardown() {
          this._refCount = 0;
          const { _connection: e } = this;
          (this._subject = this._connection = null),
            null == e || e.unsubscribe();
        }
        connect() {
          let e = this._connection;
          if (!e) {
            e = this._connection = new Le();
            const t = this.getSubject();
            e.add(
              this.source.subscribe(
                new De(
                  t,
                  void 0,
                  () => {
                    this._teardown(), t.complete();
                  },
                  (i) => {
                    this._teardown(), t.error(i);
                  },
                  () => this._teardown()
                )
              )
            ),
              e.closed && ((this._connection = null), (e = Le.EMPTY));
          }
          return e;
        }
        refCount() {
          return oE()(this);
        }
      }
      function ni(n, e) {
        return Fe((t, i) => {
          let r = null,
            s = 0,
            o = !1;
          const a = () => o && !r && i.complete();
          t.subscribe(
            new De(
              i,
              (l) => {
                null == r || r.unsubscribe();
                let c = 0;
                const u = s++;
                St(n(l, u)).subscribe(
                  (r = new De(
                    i,
                    (d) => i.next(e ? e(l, d, u, c++) : d),
                    () => {
                      (r = null), a();
                    }
                  ))
                );
              },
              () => {
                (o = !0), a();
              }
            )
          );
        });
      }
      function us(...n) {
        const e = Es(n);
        return Fe((t, i) => {
          (e ? qf(n, t, e) : qf(n, t)).subscribe(i);
        });
      }
      function sB(n, e, t, i, r) {
        return (s, o) => {
          let a = t,
            l = e,
            c = 0;
          s.subscribe(
            new De(
              o,
              (u) => {
                const d = c++;
                (l = a ? n(l, u, d) : ((a = !0), u)), i && o.next(l);
              },
              r &&
                (() => {
                  a && o.next(l), o.complete();
                })
            )
          );
        };
      }
      function aE(n, e) {
        return Fe(sB(n, e, arguments.length >= 2, !0));
      }
      function Si(n) {
        return Fe((e, t) => {
          let s,
            i = null,
            r = !1;
          (i = e.subscribe(
            new De(t, void 0, void 0, (o) => {
              (s = St(n(o, Si(n)(e)))),
                i ? (i.unsubscribe(), (i = null), s.subscribe(t)) : (r = !0);
            })
          )),
            r && (i.unsubscribe(), (i = null), s.subscribe(t));
        });
      }
      function ds(n, e) {
        return ae(e) ? Ke(n, e, 1) : Ke(n, 1);
      }
      function Kf(n) {
        return n <= 0
          ? () => wn
          : Fe((e, t) => {
              let i = [];
              e.subscribe(
                new De(
                  t,
                  (r) => {
                    i.push(r), n < i.length && i.shift();
                  },
                  () => {
                    for (const r of i) t.next(r);
                    t.complete();
                  },
                  void 0,
                  () => {
                    i = null;
                  }
                )
              );
            });
      }
      function lE(n = oB) {
        return Fe((e, t) => {
          let i = !1;
          e.subscribe(
            new De(
              t,
              (r) => {
                (i = !0), t.next(r);
              },
              () => (i ? t.complete() : t.error(n()))
            )
          );
        });
      }
      function oB() {
        return new oc();
      }
      function cE(n) {
        return Fe((e, t) => {
          let i = !1;
          e.subscribe(
            new De(
              t,
              (r) => {
                (i = !0), t.next(r);
              },
              () => {
                i || t.next(n), t.complete();
              }
            )
          );
        });
      }
      function hs(n, e) {
        const t = arguments.length >= 2;
        return (i) =>
          i.pipe(
            n ? tn((r, s) => n(r, s, i)) : ai,
            Un(1),
            t ? cE(e) : lE(() => new oc())
          );
      }
      class ii {
        constructor(e, t) {
          (this.id = e), (this.url = t);
        }
      }
      class Yf extends ii {
        constructor(e, t, i = "imperative", r = null) {
          super(e, t), (this.navigationTrigger = i), (this.restoredState = r);
        }
        toString() {
          return `NavigationStart(id: ${this.id}, url: '${this.url}')`;
        }
      }
      class Vo extends ii {
        constructor(e, t, i) {
          super(e, t), (this.urlAfterRedirects = i);
        }
        toString() {
          return `NavigationEnd(id: ${this.id}, url: '${this.url}', urlAfterRedirects: '${this.urlAfterRedirects}')`;
        }
      }
      class uE extends ii {
        constructor(e, t, i) {
          super(e, t), (this.reason = i);
        }
        toString() {
          return `NavigationCancel(id: ${this.id}, url: '${this.url}')`;
        }
      }
      class cB extends ii {
        constructor(e, t, i) {
          super(e, t), (this.error = i);
        }
        toString() {
          return `NavigationError(id: ${this.id}, url: '${this.url}', error: ${this.error})`;
        }
      }
      class uB extends ii {
        constructor(e, t, i, r) {
          super(e, t), (this.urlAfterRedirects = i), (this.state = r);
        }
        toString() {
          return `RoutesRecognized(id: ${this.id}, url: '${this.url}', urlAfterRedirects: '${this.urlAfterRedirects}', state: ${this.state})`;
        }
      }
      class dB extends ii {
        constructor(e, t, i, r) {
          super(e, t), (this.urlAfterRedirects = i), (this.state = r);
        }
        toString() {
          return `GuardsCheckStart(id: ${this.id}, url: '${this.url}', urlAfterRedirects: '${this.urlAfterRedirects}', state: ${this.state})`;
        }
      }
      class hB extends ii {
        constructor(e, t, i, r, s) {
          super(e, t),
            (this.urlAfterRedirects = i),
            (this.state = r),
            (this.shouldActivate = s);
        }
        toString() {
          return `GuardsCheckEnd(id: ${this.id}, url: '${this.url}', urlAfterRedirects: '${this.urlAfterRedirects}', state: ${this.state}, shouldActivate: ${this.shouldActivate})`;
        }
      }
      class fB extends ii {
        constructor(e, t, i, r) {
          super(e, t), (this.urlAfterRedirects = i), (this.state = r);
        }
        toString() {
          return `ResolveStart(id: ${this.id}, url: '${this.url}', urlAfterRedirects: '${this.urlAfterRedirects}', state: ${this.state})`;
        }
      }
      class pB extends ii {
        constructor(e, t, i, r) {
          super(e, t), (this.urlAfterRedirects = i), (this.state = r);
        }
        toString() {
          return `ResolveEnd(id: ${this.id}, url: '${this.url}', urlAfterRedirects: '${this.urlAfterRedirects}', state: ${this.state})`;
        }
      }
      class dE {
        constructor(e) {
          this.route = e;
        }
        toString() {
          return `RouteConfigLoadStart(path: ${this.route.path})`;
        }
      }
      class hE {
        constructor(e) {
          this.route = e;
        }
        toString() {
          return `RouteConfigLoadEnd(path: ${this.route.path})`;
        }
      }
      class gB {
        constructor(e) {
          this.snapshot = e;
        }
        toString() {
          return `ChildActivationStart(path: '${
            (this.snapshot.routeConfig && this.snapshot.routeConfig.path) || ""
          }')`;
        }
      }
      class mB {
        constructor(e) {
          this.snapshot = e;
        }
        toString() {
          return `ChildActivationEnd(path: '${
            (this.snapshot.routeConfig && this.snapshot.routeConfig.path) || ""
          }')`;
        }
      }
      class _B {
        constructor(e) {
          this.snapshot = e;
        }
        toString() {
          return `ActivationStart(path: '${
            (this.snapshot.routeConfig && this.snapshot.routeConfig.path) || ""
          }')`;
        }
      }
      class yB {
        constructor(e) {
          this.snapshot = e;
        }
        toString() {
          return `ActivationEnd(path: '${
            (this.snapshot.routeConfig && this.snapshot.routeConfig.path) || ""
          }')`;
        }
      }
      class fE {
        constructor(e, t, i) {
          (this.routerEvent = e), (this.position = t), (this.anchor = i);
        }
        toString() {
          return `Scroll(anchor: '${this.anchor}', position: '${
            this.position ? `${this.position[0]}, ${this.position[1]}` : null
          }')`;
        }
      }
      const Y = "primary";
      class vB {
        constructor(e) {
          this.params = e || {};
        }
        has(e) {
          return Object.prototype.hasOwnProperty.call(this.params, e);
        }
        get(e) {
          if (this.has(e)) {
            const t = this.params[e];
            return Array.isArray(t) ? t[0] : t;
          }
          return null;
        }
        getAll(e) {
          if (this.has(e)) {
            const t = this.params[e];
            return Array.isArray(t) ? t : [t];
          }
          return [];
        }
        get keys() {
          return Object.keys(this.params);
        }
      }
      function fs(n) {
        return new vB(n);
      }
      const pE = "ngNavigationCancelingError";
      function Zf(n) {
        const e = Error("NavigationCancelingError: " + n);
        return (e[pE] = !0), e;
      }
      function CB(n, e, t) {
        const i = t.path.split("/");
        if (
          i.length > n.length ||
          ("full" === t.pathMatch && (e.hasChildren() || i.length < n.length))
        )
          return null;
        const r = {};
        for (let s = 0; s < i.length; s++) {
          const o = i[s],
            a = n[s];
          if (o.startsWith(":")) r[o.substring(1)] = a;
          else if (o !== a.path) return null;
        }
        return { consumed: n.slice(0, i.length), posParams: r };
      }
      function Vn(n, e) {
        const t = n ? Object.keys(n) : void 0,
          i = e ? Object.keys(e) : void 0;
        if (!t || !i || t.length != i.length) return !1;
        let r;
        for (let s = 0; s < t.length; s++)
          if (((r = t[s]), !gE(n[r], e[r]))) return !1;
        return !0;
      }
      function gE(n, e) {
        if (Array.isArray(n) && Array.isArray(e)) {
          if (n.length !== e.length) return !1;
          const t = [...n].sort(),
            i = [...e].sort();
          return t.every((r, s) => i[s] === r);
        }
        return n === e;
      }
      function mE(n) {
        return Array.prototype.concat.apply([], n);
      }
      function _E(n) {
        return n.length > 0 ? n[n.length - 1] : null;
      }
      function rt(n, e) {
        for (const t in n) n.hasOwnProperty(t) && e(n[t], t);
      }
      function Bn(n) {
        return Sd(n) ? n : Js(n) ? et(Promise.resolve(n)) : H(n);
      }
      const EB = {
          exact: function bE(n, e, t) {
            if (
              !tr(n.segments, e.segments) ||
              !ac(n.segments, e.segments, t) ||
              n.numberOfChildren !== e.numberOfChildren
            )
              return !1;
            for (const i in e.children)
              if (!n.children[i] || !bE(n.children[i], e.children[i], t))
                return !1;
            return !0;
          },
          subset: CE,
        },
        yE = {
          exact: function MB(n, e) {
            return Vn(n, e);
          },
          subset: function SB(n, e) {
            return (
              Object.keys(e).length <= Object.keys(n).length &&
              Object.keys(e).every((t) => gE(n[t], e[t]))
            );
          },
          ignored: () => !0,
        };
      function vE(n, e, t) {
        return (
          EB[t.paths](n.root, e.root, t.matrixParams) &&
          yE[t.queryParams](n.queryParams, e.queryParams) &&
          !("exact" === t.fragment && n.fragment !== e.fragment)
        );
      }
      function CE(n, e, t) {
        return wE(n, e, e.segments, t);
      }
      function wE(n, e, t, i) {
        if (n.segments.length > t.length) {
          const r = n.segments.slice(0, t.length);
          return !(!tr(r, t) || e.hasChildren() || !ac(r, t, i));
        }
        if (n.segments.length === t.length) {
          if (!tr(n.segments, t) || !ac(n.segments, t, i)) return !1;
          for (const r in e.children)
            if (!n.children[r] || !CE(n.children[r], e.children[r], i))
              return !1;
          return !0;
        }
        {
          const r = t.slice(0, n.segments.length),
            s = t.slice(n.segments.length);
          return (
            !!(tr(n.segments, r) && ac(n.segments, r, i) && n.children[Y]) &&
            wE(n.children[Y], e, s, i)
          );
        }
      }
      function ac(n, e, t) {
        return e.every((i, r) => yE[t](n[r].parameters, i.parameters));
      }
      class er {
        constructor(e, t, i) {
          (this.root = e), (this.queryParams = t), (this.fragment = i);
        }
        get queryParamMap() {
          return (
            this._queryParamMap || (this._queryParamMap = fs(this.queryParams)),
            this._queryParamMap
          );
        }
        toString() {
          return OB.serialize(this);
        }
      }
      class te {
        constructor(e, t) {
          (this.segments = e),
            (this.children = t),
            (this.parent = null),
            rt(t, (i, r) => (i.parent = this));
        }
        hasChildren() {
          return this.numberOfChildren > 0;
        }
        get numberOfChildren() {
          return Object.keys(this.children).length;
        }
        toString() {
          return lc(this);
        }
      }
      class Bo {
        constructor(e, t) {
          (this.path = e), (this.parameters = t);
        }
        get parameterMap() {
          return (
            this._parameterMap || (this._parameterMap = fs(this.parameters)),
            this._parameterMap
          );
        }
        toString() {
          return AE(this);
        }
      }
      function tr(n, e) {
        return n.length === e.length && n.every((t, i) => t.path === e[i].path);
      }
      class DE {}
      class EE {
        parse(e) {
          const t = new VB(e);
          return new er(
            t.parseRootSegment(),
            t.parseQueryParams(),
            t.parseFragment()
          );
        }
        serialize(e) {
          const t = `/${jo(e.root, !0)}`,
            i = (function kB(n) {
              const e = Object.keys(n)
                .map((t) => {
                  const i = n[t];
                  return Array.isArray(i)
                    ? i.map((r) => `${cc(t)}=${cc(r)}`).join("&")
                    : `${cc(t)}=${cc(i)}`;
                })
                .filter((t) => !!t);
              return e.length ? `?${e.join("&")}` : "";
            })(e.queryParams);
          return `${t}${i}${
            "string" == typeof e.fragment
              ? `#${(function IB(n) {
                  return encodeURI(n);
                })(e.fragment)}`
              : ""
          }`;
        }
      }
      const OB = new EE();
      function lc(n) {
        return n.segments.map((e) => AE(e)).join("/");
      }
      function jo(n, e) {
        if (!n.hasChildren()) return lc(n);
        if (e) {
          const t = n.children[Y] ? jo(n.children[Y], !1) : "",
            i = [];
          return (
            rt(n.children, (r, s) => {
              s !== Y && i.push(`${s}:${jo(r, !1)}`);
            }),
            i.length > 0 ? `${t}(${i.join("//")})` : t
          );
        }
        {
          const t = (function TB(n, e) {
            let t = [];
            return (
              rt(n.children, (i, r) => {
                r === Y && (t = t.concat(e(i, r)));
              }),
              rt(n.children, (i, r) => {
                r !== Y && (t = t.concat(e(i, r)));
              }),
              t
            );
          })(n, (i, r) =>
            r === Y ? [jo(n.children[Y], !1)] : [`${r}:${jo(i, !1)}`]
          );
          return 1 === Object.keys(n.children).length && null != n.children[Y]
            ? `${lc(n)}/${t[0]}`
            : `${lc(n)}/(${t.join("//")})`;
        }
      }
      function ME(n) {
        return encodeURIComponent(n)
          .replace(/%40/g, "@")
          .replace(/%3A/gi, ":")
          .replace(/%24/g, "$")
          .replace(/%2C/gi, ",");
      }
      function cc(n) {
        return ME(n).replace(/%3B/gi, ";");
      }
      function Qf(n) {
        return ME(n)
          .replace(/\(/g, "%28")
          .replace(/\)/g, "%29")
          .replace(/%26/gi, "&");
      }
      function uc(n) {
        return decodeURIComponent(n);
      }
      function SE(n) {
        return uc(n.replace(/\+/g, "%20"));
      }
      function AE(n) {
        return `${Qf(n.path)}${(function xB(n) {
          return Object.keys(n)
            .map((e) => `;${Qf(e)}=${Qf(n[e])}`)
            .join("");
        })(n.parameters)}`;
      }
      const FB = /^[^\/()?;=#]+/;
      function dc(n) {
        const e = n.match(FB);
        return e ? e[0] : "";
      }
      const RB = /^[^=?&#]+/,
        NB = /^[^&#]+/;
      class VB {
        constructor(e) {
          (this.url = e), (this.remaining = e);
        }
        parseRootSegment() {
          return (
            this.consumeOptional("/"),
            "" === this.remaining ||
            this.peekStartsWith("?") ||
            this.peekStartsWith("#")
              ? new te([], {})
              : new te([], this.parseChildren())
          );
        }
        parseQueryParams() {
          const e = {};
          if (this.consumeOptional("?"))
            do {
              this.parseQueryParam(e);
            } while (this.consumeOptional("&"));
          return e;
        }
        parseFragment() {
          return this.consumeOptional("#")
            ? decodeURIComponent(this.remaining)
            : null;
        }
        parseChildren() {
          if ("" === this.remaining) return {};
          this.consumeOptional("/");
          const e = [];
          for (
            this.peekStartsWith("(") || e.push(this.parseSegment());
            this.peekStartsWith("/") &&
            !this.peekStartsWith("//") &&
            !this.peekStartsWith("/(");

          )
            this.capture("/"), e.push(this.parseSegment());
          let t = {};
          this.peekStartsWith("/(") &&
            (this.capture("/"), (t = this.parseParens(!0)));
          let i = {};
          return (
            this.peekStartsWith("(") && (i = this.parseParens(!1)),
            (e.length > 0 || Object.keys(t).length > 0) &&
              (i[Y] = new te(e, t)),
            i
          );
        }
        parseSegment() {
          const e = dc(this.remaining);
          if ("" === e && this.peekStartsWith(";"))
            throw new Error(
              `Empty path url segment cannot have parameters: '${this.remaining}'.`
            );
          return this.capture(e), new Bo(uc(e), this.parseMatrixParams());
        }
        parseMatrixParams() {
          const e = {};
          for (; this.consumeOptional(";"); ) this.parseParam(e);
          return e;
        }
        parseParam(e) {
          const t = dc(this.remaining);
          if (!t) return;
          this.capture(t);
          let i = "";
          if (this.consumeOptional("=")) {
            const r = dc(this.remaining);
            r && ((i = r), this.capture(i));
          }
          e[uc(t)] = uc(i);
        }
        parseQueryParam(e) {
          const t = (function PB(n) {
            const e = n.match(RB);
            return e ? e[0] : "";
          })(this.remaining);
          if (!t) return;
          this.capture(t);
          let i = "";
          if (this.consumeOptional("=")) {
            const o = (function LB(n) {
              const e = n.match(NB);
              return e ? e[0] : "";
            })(this.remaining);
            o && ((i = o), this.capture(i));
          }
          const r = SE(t),
            s = SE(i);
          if (e.hasOwnProperty(r)) {
            let o = e[r];
            Array.isArray(o) || ((o = [o]), (e[r] = o)), o.push(s);
          } else e[r] = s;
        }
        parseParens(e) {
          const t = {};
          for (
            this.capture("(");
            !this.consumeOptional(")") && this.remaining.length > 0;

          ) {
            const i = dc(this.remaining),
              r = this.remaining[i.length];
            if ("/" !== r && ")" !== r && ";" !== r)
              throw new Error(`Cannot parse url '${this.url}'`);
            let s;
            i.indexOf(":") > -1
              ? ((s = i.substr(0, i.indexOf(":"))),
                this.capture(s),
                this.capture(":"))
              : e && (s = Y);
            const o = this.parseChildren();
            (t[s] = 1 === Object.keys(o).length ? o[Y] : new te([], o)),
              this.consumeOptional("//");
          }
          return t;
        }
        peekStartsWith(e) {
          return this.remaining.startsWith(e);
        }
        consumeOptional(e) {
          return (
            !!this.peekStartsWith(e) &&
            ((this.remaining = this.remaining.substring(e.length)), !0)
          );
        }
        capture(e) {
          if (!this.consumeOptional(e)) throw new Error(`Expected "${e}".`);
        }
      }
      class TE {
        constructor(e) {
          this._root = e;
        }
        get root() {
          return this._root.value;
        }
        parent(e) {
          const t = this.pathFromRoot(e);
          return t.length > 1 ? t[t.length - 2] : null;
        }
        children(e) {
          const t = Xf(e, this._root);
          return t ? t.children.map((i) => i.value) : [];
        }
        firstChild(e) {
          const t = Xf(e, this._root);
          return t && t.children.length > 0 ? t.children[0].value : null;
        }
        siblings(e) {
          const t = Jf(e, this._root);
          return t.length < 2
            ? []
            : t[t.length - 2].children
                .map((r) => r.value)
                .filter((r) => r !== e);
        }
        pathFromRoot(e) {
          return Jf(e, this._root).map((t) => t.value);
        }
      }
      function Xf(n, e) {
        if (n === e.value) return e;
        for (const t of e.children) {
          const i = Xf(n, t);
          if (i) return i;
        }
        return null;
      }
      function Jf(n, e) {
        if (n === e.value) return [e];
        for (const t of e.children) {
          const i = Jf(n, t);
          if (i.length) return i.unshift(e), i;
        }
        return [];
      }
      class ri {
        constructor(e, t) {
          (this.value = e), (this.children = t);
        }
        toString() {
          return `TreeNode(${this.value})`;
        }
      }
      function ps(n) {
        const e = {};
        return n && n.children.forEach((t) => (e[t.value.outlet] = t)), e;
      }
      class OE extends TE {
        constructor(e, t) {
          super(e), (this.snapshot = t), ep(this, e);
        }
        toString() {
          return this.snapshot.toString();
        }
      }
      function IE(n, e) {
        const t = (function BB(n, e) {
            const o = new hc([], {}, {}, "", {}, Y, e, null, n.root, -1, {});
            return new kE("", new ri(o, []));
          })(n, e),
          i = new en([new Bo("", {})]),
          r = new en({}),
          s = new en({}),
          o = new en({}),
          a = new en(""),
          l = new gs(i, r, o, a, s, Y, e, t.root);
        return (l.snapshot = t.root), new OE(new ri(l, []), t);
      }
      class gs {
        constructor(e, t, i, r, s, o, a, l) {
          (this.url = e),
            (this.params = t),
            (this.queryParams = i),
            (this.fragment = r),
            (this.data = s),
            (this.outlet = o),
            (this.component = a),
            (this._futureSnapshot = l);
        }
        get routeConfig() {
          return this._futureSnapshot.routeConfig;
        }
        get root() {
          return this._routerState.root;
        }
        get parent() {
          return this._routerState.parent(this);
        }
        get firstChild() {
          return this._routerState.firstChild(this);
        }
        get children() {
          return this._routerState.children(this);
        }
        get pathFromRoot() {
          return this._routerState.pathFromRoot(this);
        }
        get paramMap() {
          return (
            this._paramMap ||
              (this._paramMap = this.params.pipe(re((e) => fs(e)))),
            this._paramMap
          );
        }
        get queryParamMap() {
          return (
            this._queryParamMap ||
              (this._queryParamMap = this.queryParams.pipe(re((e) => fs(e)))),
            this._queryParamMap
          );
        }
        toString() {
          return this.snapshot
            ? this.snapshot.toString()
            : `Future(${this._futureSnapshot})`;
        }
      }
      function xE(n, e = "emptyOnly") {
        const t = n.pathFromRoot;
        let i = 0;
        if ("always" !== e)
          for (i = t.length - 1; i >= 1; ) {
            const r = t[i],
              s = t[i - 1];
            if (r.routeConfig && "" === r.routeConfig.path) i--;
            else {
              if (s.component) break;
              i--;
            }
          }
        return (function jB(n) {
          return n.reduce(
            (e, t) => ({
              params: Object.assign(Object.assign({}, e.params), t.params),
              data: Object.assign(Object.assign({}, e.data), t.data),
              resolve: Object.assign(
                Object.assign({}, e.resolve),
                t._resolvedData
              ),
            }),
            { params: {}, data: {}, resolve: {} }
          );
        })(t.slice(i));
      }
      class hc {
        constructor(e, t, i, r, s, o, a, l, c, u, d) {
          (this.url = e),
            (this.params = t),
            (this.queryParams = i),
            (this.fragment = r),
            (this.data = s),
            (this.outlet = o),
            (this.component = a),
            (this.routeConfig = l),
            (this._urlSegment = c),
            (this._lastPathIndex = u),
            (this._resolve = d);
        }
        get root() {
          return this._routerState.root;
        }
        get parent() {
          return this._routerState.parent(this);
        }
        get firstChild() {
          return this._routerState.firstChild(this);
        }
        get children() {
          return this._routerState.children(this);
        }
        get pathFromRoot() {
          return this._routerState.pathFromRoot(this);
        }
        get paramMap() {
          return (
            this._paramMap || (this._paramMap = fs(this.params)), this._paramMap
          );
        }
        get queryParamMap() {
          return (
            this._queryParamMap || (this._queryParamMap = fs(this.queryParams)),
            this._queryParamMap
          );
        }
        toString() {
          return `Route(url:'${this.url
            .map((i) => i.toString())
            .join("/")}', path:'${
            this.routeConfig ? this.routeConfig.path : ""
          }')`;
        }
      }
      class kE extends TE {
        constructor(e, t) {
          super(t), (this.url = e), ep(this, t);
        }
        toString() {
          return FE(this._root);
        }
      }
      function ep(n, e) {
        (e.value._routerState = n), e.children.forEach((t) => ep(n, t));
      }
      function FE(n) {
        const e =
          n.children.length > 0 ? ` { ${n.children.map(FE).join(", ")} } ` : "";
        return `${n.value}${e}`;
      }
      function tp(n) {
        if (n.snapshot) {
          const e = n.snapshot,
            t = n._futureSnapshot;
          (n.snapshot = t),
            Vn(e.queryParams, t.queryParams) ||
              n.queryParams.next(t.queryParams),
            e.fragment !== t.fragment && n.fragment.next(t.fragment),
            Vn(e.params, t.params) || n.params.next(t.params),
            (function wB(n, e) {
              if (n.length !== e.length) return !1;
              for (let t = 0; t < n.length; ++t) if (!Vn(n[t], e[t])) return !1;
              return !0;
            })(e.url, t.url) || n.url.next(t.url),
            Vn(e.data, t.data) || n.data.next(t.data);
        } else
          (n.snapshot = n._futureSnapshot), n.data.next(n._futureSnapshot.data);
      }
      function np(n, e) {
        const t =
          Vn(n.params, e.params) &&
          (function AB(n, e) {
            return (
              tr(n, e) && n.every((t, i) => Vn(t.parameters, e[i].parameters))
            );
          })(n.url, e.url);
        return (
          t &&
          !(!n.parent != !e.parent) &&
          (!n.parent || np(n.parent, e.parent))
        );
      }
      function Ho(n, e, t) {
        if (t && n.shouldReuseRoute(e.value, t.value.snapshot)) {
          const i = t.value;
          i._futureSnapshot = e.value;
          const r = (function UB(n, e, t) {
            return e.children.map((i) => {
              for (const r of t.children)
                if (n.shouldReuseRoute(i.value, r.value.snapshot))
                  return Ho(n, i, r);
              return Ho(n, i);
            });
          })(n, e, t);
          return new ri(i, r);
        }
        {
          if (n.shouldAttach(e.value)) {
            const s = n.retrieve(e.value);
            if (null !== s) {
              const o = s.route;
              return (
                (o.value._futureSnapshot = e.value),
                (o.children = e.children.map((a) => Ho(n, a))),
                o
              );
            }
          }
          const i = (function $B(n) {
              return new gs(
                new en(n.url),
                new en(n.params),
                new en(n.queryParams),
                new en(n.fragment),
                new en(n.data),
                n.outlet,
                n.component,
                n
              );
            })(e.value),
            r = e.children.map((s) => Ho(n, s));
          return new ri(i, r);
        }
      }
      function fc(n) {
        return (
          "object" == typeof n && null != n && !n.outlets && !n.segmentPath
        );
      }
      function Uo(n) {
        return "object" == typeof n && null != n && n.outlets;
      }
      function ip(n, e, t, i, r) {
        let s = {};
        return (
          i &&
            rt(i, (o, a) => {
              s[a] = Array.isArray(o) ? o.map((l) => `${l}`) : `${o}`;
            }),
          new er(t.root === n ? e : RE(t.root, n, e), s, r)
        );
      }
      function RE(n, e, t) {
        const i = {};
        return (
          rt(n.children, (r, s) => {
            i[s] = r === e ? t : RE(r, e, t);
          }),
          new te(n.segments, i)
        );
      }
      class PE {
        constructor(e, t, i) {
          if (
            ((this.isAbsolute = e),
            (this.numberOfDoubleDots = t),
            (this.commands = i),
            e && i.length > 0 && fc(i[0]))
          )
            throw new Error("Root segment cannot have matrix parameters");
          const r = i.find(Uo);
          if (r && r !== _E(i))
            throw new Error("{outlets:{}} has to be the last command");
        }
        toRoot() {
          return (
            this.isAbsolute &&
            1 === this.commands.length &&
            "/" == this.commands[0]
          );
        }
      }
      class rp {
        constructor(e, t, i) {
          (this.segmentGroup = e), (this.processChildren = t), (this.index = i);
        }
      }
      function NE(n, e, t) {
        if (
          (n || (n = new te([], {})),
          0 === n.segments.length && n.hasChildren())
        )
          return pc(n, e, t);
        const i = (function YB(n, e, t) {
            let i = 0,
              r = e;
            const s = { match: !1, pathIndex: 0, commandIndex: 0 };
            for (; r < n.segments.length; ) {
              if (i >= t.length) return s;
              const o = n.segments[r],
                a = t[i];
              if (Uo(a)) break;
              const l = `${a}`,
                c = i < t.length - 1 ? t[i + 1] : null;
              if (r > 0 && void 0 === l) break;
              if (l && c && "object" == typeof c && void 0 === c.outlets) {
                if (!VE(l, c, o)) return s;
                i += 2;
              } else {
                if (!VE(l, {}, o)) return s;
                i++;
              }
              r++;
            }
            return { match: !0, pathIndex: r, commandIndex: i };
          })(n, e, t),
          r = t.slice(i.commandIndex);
        if (i.match && i.pathIndex < n.segments.length) {
          const s = new te(n.segments.slice(0, i.pathIndex), {});
          return (
            (s.children[Y] = new te(n.segments.slice(i.pathIndex), n.children)),
            pc(s, 0, r)
          );
        }
        return i.match && 0 === r.length
          ? new te(n.segments, {})
          : i.match && !n.hasChildren()
          ? sp(n, e, t)
          : i.match
          ? pc(n, 0, r)
          : sp(n, e, t);
      }
      function pc(n, e, t) {
        if (0 === t.length) return new te(n.segments, {});
        {
          const i = (function KB(n) {
              return Uo(n[0]) ? n[0].outlets : { [Y]: n };
            })(t),
            r = {};
          return (
            rt(i, (s, o) => {
              "string" == typeof s && (s = [s]),
                null !== s && (r[o] = NE(n.children[o], e, s));
            }),
            rt(n.children, (s, o) => {
              void 0 === i[o] && (r[o] = s);
            }),
            new te(n.segments, r)
          );
        }
      }
      function sp(n, e, t) {
        const i = n.segments.slice(0, e);
        let r = 0;
        for (; r < t.length; ) {
          const s = t[r];
          if (Uo(s)) {
            const l = ZB(s.outlets);
            return new te(i, l);
          }
          if (0 === r && fc(t[0])) {
            i.push(new Bo(n.segments[e].path, LE(t[0]))), r++;
            continue;
          }
          const o = Uo(s) ? s.outlets[Y] : `${s}`,
            a = r < t.length - 1 ? t[r + 1] : null;
          o && a && fc(a)
            ? (i.push(new Bo(o, LE(a))), (r += 2))
            : (i.push(new Bo(o, {})), r++);
        }
        return new te(i, {});
      }
      function ZB(n) {
        const e = {};
        return (
          rt(n, (t, i) => {
            "string" == typeof t && (t = [t]),
              null !== t && (e[i] = sp(new te([], {}), 0, t));
          }),
          e
        );
      }
      function LE(n) {
        const e = {};
        return rt(n, (t, i) => (e[i] = `${t}`)), e;
      }
      function VE(n, e, t) {
        return n == t.path && Vn(e, t.parameters);
      }
      class XB {
        constructor(e, t, i, r) {
          (this.routeReuseStrategy = e),
            (this.futureState = t),
            (this.currState = i),
            (this.forwardEvent = r);
        }
        activate(e) {
          const t = this.futureState._root,
            i = this.currState ? this.currState._root : null;
          this.deactivateChildRoutes(t, i, e),
            tp(this.futureState.root),
            this.activateChildRoutes(t, i, e);
        }
        deactivateChildRoutes(e, t, i) {
          const r = ps(t);
          e.children.forEach((s) => {
            const o = s.value.outlet;
            this.deactivateRoutes(s, r[o], i), delete r[o];
          }),
            rt(r, (s, o) => {
              this.deactivateRouteAndItsChildren(s, i);
            });
        }
        deactivateRoutes(e, t, i) {
          const r = e.value,
            s = t ? t.value : null;
          if (r === s)
            if (r.component) {
              const o = i.getContext(r.outlet);
              o && this.deactivateChildRoutes(e, t, o.children);
            } else this.deactivateChildRoutes(e, t, i);
          else s && this.deactivateRouteAndItsChildren(t, i);
        }
        deactivateRouteAndItsChildren(e, t) {
          e.value.component &&
          this.routeReuseStrategy.shouldDetach(e.value.snapshot)
            ? this.detachAndStoreRouteSubtree(e, t)
            : this.deactivateRouteAndOutlet(e, t);
        }
        detachAndStoreRouteSubtree(e, t) {
          const i = t.getContext(e.value.outlet),
            r = i && e.value.component ? i.children : t,
            s = ps(e);
          for (const o of Object.keys(s))
            this.deactivateRouteAndItsChildren(s[o], r);
          if (i && i.outlet) {
            const o = i.outlet.detach(),
              a = i.children.onOutletDeactivated();
            this.routeReuseStrategy.store(e.value.snapshot, {
              componentRef: o,
              route: e,
              contexts: a,
            });
          }
        }
        deactivateRouteAndOutlet(e, t) {
          const i = t.getContext(e.value.outlet),
            r = i && e.value.component ? i.children : t,
            s = ps(e);
          for (const o of Object.keys(s))
            this.deactivateRouteAndItsChildren(s[o], r);
          i &&
            i.outlet &&
            (i.outlet.deactivate(),
            i.children.onOutletDeactivated(),
            (i.attachRef = null),
            (i.resolver = null),
            (i.route = null));
        }
        activateChildRoutes(e, t, i) {
          const r = ps(t);
          e.children.forEach((s) => {
            this.activateRoutes(s, r[s.value.outlet], i),
              this.forwardEvent(new yB(s.value.snapshot));
          }),
            e.children.length && this.forwardEvent(new mB(e.value.snapshot));
        }
        activateRoutes(e, t, i) {
          const r = e.value,
            s = t ? t.value : null;
          if ((tp(r), r === s))
            if (r.component) {
              const o = i.getOrCreateContext(r.outlet);
              this.activateChildRoutes(e, t, o.children);
            } else this.activateChildRoutes(e, t, i);
          else if (r.component) {
            const o = i.getOrCreateContext(r.outlet);
            if (this.routeReuseStrategy.shouldAttach(r.snapshot)) {
              const a = this.routeReuseStrategy.retrieve(r.snapshot);
              this.routeReuseStrategy.store(r.snapshot, null),
                o.children.onOutletReAttached(a.contexts),
                (o.attachRef = a.componentRef),
                (o.route = a.route.value),
                o.outlet && o.outlet.attach(a.componentRef, a.route.value),
                tp(a.route.value),
                this.activateChildRoutes(e, null, o.children);
            } else {
              const a = (function JB(n) {
                  for (let e = n.parent; e; e = e.parent) {
                    const t = e.routeConfig;
                    if (t && t._loadedConfig) return t._loadedConfig;
                    if (t && t.component) return null;
                  }
                  return null;
                })(r.snapshot),
                l = a ? a.module.componentFactoryResolver : null;
              (o.attachRef = null),
                (o.route = r),
                (o.resolver = l),
                o.outlet && o.outlet.activateWith(r, l),
                this.activateChildRoutes(e, null, o.children);
            }
          } else this.activateChildRoutes(e, null, i);
        }
      }
      class op {
        constructor(e, t) {
          (this.routes = e), (this.module = t);
        }
      }
      function Ai(n) {
        return "function" == typeof n;
      }
      function nr(n) {
        return n instanceof er;
      }
      const $o = Symbol("INITIAL_VALUE");
      function zo() {
        return ni((n) =>
          (function tB(...n) {
            const e = Es(n),
              t = Xp(n),
              { args: i, keys: r } = bC(n);
            if (0 === i.length) return et([], e);
            const s = new fe(
              (function nB(n, e, t = ai) {
                return (i) => {
                  sE(
                    e,
                    () => {
                      const { length: r } = n,
                        s = new Array(r);
                      let o = r,
                        a = r;
                      for (let l = 0; l < r; l++)
                        sE(
                          e,
                          () => {
                            const c = et(n[l], e);
                            let u = !1;
                            c.subscribe(
                              new De(
                                i,
                                (d) => {
                                  (s[l] = d),
                                    u || ((u = !0), a--),
                                    a || i.next(t(s.slice()));
                                },
                                () => {
                                  --o || i.complete();
                                }
                              )
                            );
                          },
                          i
                        );
                    },
                    i
                  );
                };
              })(i, e, r ? (o) => CC(r, o) : ai)
            );
            return t ? s.pipe(Ih(t)) : s;
          })(n.map((e) => e.pipe(Un(1), us($o)))).pipe(
            aE((e, t) => {
              let i = !1;
              return t.reduce(
                (r, s, o) =>
                  r !== $o
                    ? r
                    : (s === $o && (i = !0),
                      i || (!1 !== s && o !== t.length - 1 && !nr(s)) ? r : s),
                e
              );
            }, $o),
            tn((e) => e !== $o),
            re((e) => (nr(e) ? e : !0 === e)),
            Un(1)
          )
        );
      }
      class sj {
        constructor() {
          (this.outlet = null),
            (this.route = null),
            (this.resolver = null),
            (this.children = new Go()),
            (this.attachRef = null);
        }
      }
      class Go {
        constructor() {
          this.contexts = new Map();
        }
        onChildOutletCreated(e, t) {
          const i = this.getOrCreateContext(e);
          (i.outlet = t), this.contexts.set(e, i);
        }
        onChildOutletDestroyed(e) {
          const t = this.getContext(e);
          t && ((t.outlet = null), (t.attachRef = null));
        }
        onOutletDeactivated() {
          const e = this.contexts;
          return (this.contexts = new Map()), e;
        }
        onOutletReAttached(e) {
          this.contexts = e;
        }
        getOrCreateContext(e) {
          let t = this.getContext(e);
          return t || ((t = new sj()), this.contexts.set(e, t)), t;
        }
        getContext(e) {
          return this.contexts.get(e) || null;
        }
      }
      let ap = (() => {
        class n {
          constructor(t, i, r, s, o) {
            (this.parentContexts = t),
              (this.location = i),
              (this.resolver = r),
              (this.changeDetector = o),
              (this.activated = null),
              (this._activatedRoute = null),
              (this.activateEvents = new Q()),
              (this.deactivateEvents = new Q()),
              (this.attachEvents = new Q()),
              (this.detachEvents = new Q()),
              (this.name = s || Y),
              t.onChildOutletCreated(this.name, this);
          }
          ngOnDestroy() {
            this.parentContexts.onChildOutletDestroyed(this.name);
          }
          ngOnInit() {
            if (!this.activated) {
              const t = this.parentContexts.getContext(this.name);
              t &&
                t.route &&
                (t.attachRef
                  ? this.attach(t.attachRef, t.route)
                  : this.activateWith(t.route, t.resolver || null));
            }
          }
          get isActivated() {
            return !!this.activated;
          }
          get component() {
            if (!this.activated) throw new Error("Outlet is not activated");
            return this.activated.instance;
          }
          get activatedRoute() {
            if (!this.activated) throw new Error("Outlet is not activated");
            return this._activatedRoute;
          }
          get activatedRouteData() {
            return this._activatedRoute
              ? this._activatedRoute.snapshot.data
              : {};
          }
          detach() {
            if (!this.activated) throw new Error("Outlet is not activated");
            this.location.detach();
            const t = this.activated;
            return (
              (this.activated = null),
              (this._activatedRoute = null),
              this.detachEvents.emit(t.instance),
              t
            );
          }
          attach(t, i) {
            (this.activated = t),
              (this._activatedRoute = i),
              this.location.insert(t.hostView),
              this.attachEvents.emit(t.instance);
          }
          deactivate() {
            if (this.activated) {
              const t = this.component;
              this.activated.destroy(),
                (this.activated = null),
                (this._activatedRoute = null),
                this.deactivateEvents.emit(t);
            }
          }
          activateWith(t, i) {
            if (this.isActivated)
              throw new Error("Cannot activate an already activated outlet");
            this._activatedRoute = t;
            const o = (i = i || this.resolver).resolveComponentFactory(
                t._futureSnapshot.routeConfig.component
              ),
              a = this.parentContexts.getOrCreateContext(this.name).children,
              l = new oj(t, a, this.location.injector);
            (this.activated = this.location.createComponent(
              o,
              this.location.length,
              l
            )),
              this.changeDetector.markForCheck(),
              this.activateEvents.emit(this.activated.instance);
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(_(Go), _(Zt), _($i), Bi("name"), _(vi));
          }),
          (n.ɵdir = x({
            type: n,
            selectors: [["router-outlet"]],
            outputs: {
              activateEvents: "activate",
              deactivateEvents: "deactivate",
              attachEvents: "attach",
              detachEvents: "detach",
            },
            exportAs: ["outlet"],
          })),
          n
        );
      })();
      class oj {
        constructor(e, t, i) {
          (this.route = e), (this.childContexts = t), (this.parent = i);
        }
        get(e, t) {
          return e === gs
            ? this.route
            : e === Go
            ? this.childContexts
            : this.parent.get(e, t);
        }
      }
      let BE = (() => {
        class n {}
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵcmp = Dn({
            type: n,
            selectors: [["ng-component"]],
            decls: 1,
            vars: 0,
            template: function (t, i) {
              1 & t && Me(0, "router-outlet");
            },
            directives: [ap],
            encapsulation: 2,
          })),
          n
        );
      })();
      function jE(n, e = "") {
        for (let t = 0; t < n.length; t++) {
          const i = n[t];
          aj(i, lj(e, i));
        }
      }
      function aj(n, e) {
        n.children && jE(n.children, e);
      }
      function lj(n, e) {
        return e
          ? n || e.path
            ? n && !e.path
              ? `${n}/`
              : !n && e.path
              ? e.path
              : `${n}/${e.path}`
            : ""
          : n;
      }
      function lp(n) {
        const e = n.children && n.children.map(lp),
          t = e
            ? Object.assign(Object.assign({}, n), { children: e })
            : Object.assign({}, n);
        return (
          !t.component &&
            (e || t.loadChildren) &&
            t.outlet &&
            t.outlet !== Y &&
            (t.component = BE),
          t
        );
      }
      function sn(n) {
        return n.outlet || Y;
      }
      function HE(n, e) {
        const t = n.filter((i) => sn(i) === e);
        return t.push(...n.filter((i) => sn(i) !== e)), t;
      }
      const UE = {
        matched: !1,
        consumedSegments: [],
        lastChild: 0,
        parameters: {},
        positionalParamSegments: {},
      };
      function gc(n, e, t) {
        var i;
        if ("" === e.path)
          return "full" === e.pathMatch && (n.hasChildren() || t.length > 0)
            ? Object.assign({}, UE)
            : {
                matched: !0,
                consumedSegments: [],
                lastChild: 0,
                parameters: {},
                positionalParamSegments: {},
              };
        const s = (e.matcher || CB)(t, n, e);
        if (!s) return Object.assign({}, UE);
        const o = {};
        rt(s.posParams, (l, c) => {
          o[c] = l.path;
        });
        const a =
          s.consumed.length > 0
            ? Object.assign(
                Object.assign({}, o),
                s.consumed[s.consumed.length - 1].parameters
              )
            : o;
        return {
          matched: !0,
          consumedSegments: s.consumed,
          lastChild: s.consumed.length,
          parameters: a,
          positionalParamSegments:
            null !== (i = s.posParams) && void 0 !== i ? i : {},
        };
      }
      function mc(n, e, t, i, r = "corrected") {
        if (
          t.length > 0 &&
          (function dj(n, e, t) {
            return t.some((i) => _c(n, e, i) && sn(i) !== Y);
          })(n, t, i)
        ) {
          const o = new te(
            e,
            (function uj(n, e, t, i) {
              const r = {};
              (r[Y] = i),
                (i._sourceSegment = n),
                (i._segmentIndexShift = e.length);
              for (const s of t)
                if ("" === s.path && sn(s) !== Y) {
                  const o = new te([], {});
                  (o._sourceSegment = n),
                    (o._segmentIndexShift = e.length),
                    (r[sn(s)] = o);
                }
              return r;
            })(n, e, i, new te(t, n.children))
          );
          return (
            (o._sourceSegment = n),
            (o._segmentIndexShift = e.length),
            { segmentGroup: o, slicedSegments: [] }
          );
        }
        if (
          0 === t.length &&
          (function hj(n, e, t) {
            return t.some((i) => _c(n, e, i));
          })(n, t, i)
        ) {
          const o = new te(
            n.segments,
            (function cj(n, e, t, i, r, s) {
              const o = {};
              for (const a of i)
                if (_c(n, t, a) && !r[sn(a)]) {
                  const l = new te([], {});
                  (l._sourceSegment = n),
                    (l._segmentIndexShift =
                      "legacy" === s ? n.segments.length : e.length),
                    (o[sn(a)] = l);
                }
              return Object.assign(Object.assign({}, r), o);
            })(n, e, t, i, n.children, r)
          );
          return (
            (o._sourceSegment = n),
            (o._segmentIndexShift = e.length),
            { segmentGroup: o, slicedSegments: t }
          );
        }
        const s = new te(n.segments, n.children);
        return (
          (s._sourceSegment = n),
          (s._segmentIndexShift = e.length),
          { segmentGroup: s, slicedSegments: t }
        );
      }
      function _c(n, e, t) {
        return (
          (!(n.hasChildren() || e.length > 0) || "full" !== t.pathMatch) &&
          "" === t.path
        );
      }
      function $E(n, e, t, i) {
        return (
          !!(sn(n) === i || (i !== Y && _c(e, t, n))) &&
          ("**" === n.path || gc(e, n, t).matched)
        );
      }
      function zE(n, e, t) {
        return 0 === e.length && !n.children[t];
      }
      class qo {
        constructor(e) {
          this.segmentGroup = e || null;
        }
      }
      class GE {
        constructor(e) {
          this.urlTree = e;
        }
      }
      function yc(n) {
        return new fe((e) => e.error(new qo(n)));
      }
      function qE(n) {
        return new fe((e) => e.error(new GE(n)));
      }
      function fj(n) {
        return new fe((e) =>
          e.error(
            new Error(
              `Only absolute redirects can have named outlets. redirectTo: '${n}'`
            )
          )
        );
      }
      class mj {
        constructor(e, t, i, r, s) {
          (this.configLoader = t),
            (this.urlSerializer = i),
            (this.urlTree = r),
            (this.config = s),
            (this.allowRedirects = !0),
            (this.ngModule = e.get(Zn));
        }
        apply() {
          const e = mc(this.urlTree.root, [], [], this.config).segmentGroup,
            t = new te(e.segments, e.children);
          return this.expandSegmentGroup(this.ngModule, this.config, t, Y)
            .pipe(
              re((s) =>
                this.createUrlTree(
                  cp(s),
                  this.urlTree.queryParams,
                  this.urlTree.fragment
                )
              )
            )
            .pipe(
              Si((s) => {
                if (s instanceof GE)
                  return (this.allowRedirects = !1), this.match(s.urlTree);
                throw s instanceof qo ? this.noMatchError(s) : s;
              })
            );
        }
        match(e) {
          return this.expandSegmentGroup(this.ngModule, this.config, e.root, Y)
            .pipe(
              re((r) => this.createUrlTree(cp(r), e.queryParams, e.fragment))
            )
            .pipe(
              Si((r) => {
                throw r instanceof qo ? this.noMatchError(r) : r;
              })
            );
        }
        noMatchError(e) {
          return new Error(
            `Cannot match any routes. URL Segment: '${e.segmentGroup}'`
          );
        }
        createUrlTree(e, t, i) {
          const r = e.segments.length > 0 ? new te([], { [Y]: e }) : e;
          return new er(r, t, i);
        }
        expandSegmentGroup(e, t, i, r) {
          return 0 === i.segments.length && i.hasChildren()
            ? this.expandChildren(e, t, i).pipe(re((s) => new te([], s)))
            : this.expandSegment(e, i, t, i.segments, r, !0);
        }
        expandChildren(e, t, i) {
          const r = [];
          for (const s of Object.keys(i.children))
            "primary" === s ? r.unshift(s) : r.push(s);
          return et(r).pipe(
            ds((s) => {
              const o = i.children[s],
                a = HE(t, s);
              return this.expandSegmentGroup(e, a, o, s).pipe(
                re((l) => ({ segment: l, outlet: s }))
              );
            }),
            aE((s, o) => ((s[o.outlet] = o.segment), s), {}),
            (function aB(n, e) {
              const t = arguments.length >= 2;
              return (i) =>
                i.pipe(
                  n ? tn((r, s) => n(r, s, i)) : ai,
                  Kf(1),
                  t ? cE(e) : lE(() => new oc())
                );
            })()
          );
        }
        expandSegment(e, t, i, r, s, o) {
          return et(i).pipe(
            ds((a) =>
              this.expandSegmentAgainstRoute(e, t, i, a, r, s, o).pipe(
                Si((c) => {
                  if (c instanceof qo) return H(null);
                  throw c;
                })
              )
            ),
            hs((a) => !!a),
            Si((a, l) => {
              if (a instanceof oc || "EmptyError" === a.name) {
                if (zE(t, r, s)) return H(new te([], {}));
                throw new qo(t);
              }
              throw a;
            })
          );
        }
        expandSegmentAgainstRoute(e, t, i, r, s, o, a) {
          return $E(r, t, s, o)
            ? void 0 === r.redirectTo
              ? this.matchSegmentAgainstRoute(e, t, r, s, o)
              : a && this.allowRedirects
              ? this.expandSegmentAgainstRouteUsingRedirect(e, t, i, r, s, o)
              : yc(t)
            : yc(t);
        }
        expandSegmentAgainstRouteUsingRedirect(e, t, i, r, s, o) {
          return "**" === r.path
            ? this.expandWildCardWithParamsAgainstRouteUsingRedirect(e, i, r, o)
            : this.expandRegularSegmentAgainstRouteUsingRedirect(
                e,
                t,
                i,
                r,
                s,
                o
              );
        }
        expandWildCardWithParamsAgainstRouteUsingRedirect(e, t, i, r) {
          const s = this.applyRedirectCommands([], i.redirectTo, {});
          return i.redirectTo.startsWith("/")
            ? qE(s)
            : this.lineralizeSegments(i, s).pipe(
                Ke((o) => {
                  const a = new te(o, {});
                  return this.expandSegment(e, a, t, o, r, !1);
                })
              );
        }
        expandRegularSegmentAgainstRouteUsingRedirect(e, t, i, r, s, o) {
          const {
            matched: a,
            consumedSegments: l,
            lastChild: c,
            positionalParamSegments: u,
          } = gc(t, r, s);
          if (!a) return yc(t);
          const d = this.applyRedirectCommands(l, r.redirectTo, u);
          return r.redirectTo.startsWith("/")
            ? qE(d)
            : this.lineralizeSegments(r, d).pipe(
                Ke((h) =>
                  this.expandSegment(e, t, i, h.concat(s.slice(c)), o, !1)
                )
              );
        }
        matchSegmentAgainstRoute(e, t, i, r, s) {
          if ("**" === i.path)
            return i.loadChildren
              ? (i._loadedConfig
                  ? H(i._loadedConfig)
                  : this.configLoader.load(e.injector, i)
                ).pipe(re((h) => ((i._loadedConfig = h), new te(r, {}))))
              : H(new te(r, {}));
          const { matched: o, consumedSegments: a, lastChild: l } = gc(t, i, r);
          if (!o) return yc(t);
          const c = r.slice(l);
          return this.getChildConfig(e, i, r).pipe(
            Ke((d) => {
              const h = d.module,
                f = d.routes,
                { segmentGroup: p, slicedSegments: g } = mc(t, a, c, f),
                y = new te(p.segments, p.children);
              if (0 === g.length && y.hasChildren())
                return this.expandChildren(h, f, y).pipe(
                  re((A) => new te(a, A))
                );
              if (0 === f.length && 0 === g.length) return H(new te(a, {}));
              const v = sn(i) === s;
              return this.expandSegment(h, y, f, g, v ? Y : s, !0).pipe(
                re((w) => new te(a.concat(w.segments), w.children))
              );
            })
          );
        }
        getChildConfig(e, t, i) {
          return t.children
            ? H(new op(t.children, e))
            : t.loadChildren
            ? void 0 !== t._loadedConfig
              ? H(t._loadedConfig)
              : this.runCanLoadGuards(e.injector, t, i).pipe(
                  Ke((r) =>
                    r
                      ? this.configLoader
                          .load(e.injector, t)
                          .pipe(re((s) => ((t._loadedConfig = s), s)))
                      : (function pj(n) {
                          return new fe((e) =>
                            e.error(
                              Zf(
                                `Cannot load children because the guard of the route "path: '${n.path}'" returned false`
                              )
                            )
                          );
                        })(t)
                  )
                )
            : H(new op([], e));
        }
        runCanLoadGuards(e, t, i) {
          const r = t.canLoad;
          return r && 0 !== r.length
            ? H(
                r.map((o) => {
                  const a = e.get(o);
                  let l;
                  if (
                    (function tj(n) {
                      return n && Ai(n.canLoad);
                    })(a)
                  )
                    l = a.canLoad(t, i);
                  else {
                    if (!Ai(a)) throw new Error("Invalid CanLoad guard");
                    l = a(t, i);
                  }
                  return Bn(l);
                })
              ).pipe(
                zo(),
                Mt((o) => {
                  if (!nr(o)) return;
                  const a = Zf(
                    `Redirecting to "${this.urlSerializer.serialize(o)}"`
                  );
                  throw ((a.url = o), a);
                }),
                re((o) => !0 === o)
              )
            : H(!0);
        }
        lineralizeSegments(e, t) {
          let i = [],
            r = t.root;
          for (;;) {
            if (((i = i.concat(r.segments)), 0 === r.numberOfChildren))
              return H(i);
            if (r.numberOfChildren > 1 || !r.children[Y])
              return fj(e.redirectTo);
            r = r.children[Y];
          }
        }
        applyRedirectCommands(e, t, i) {
          return this.applyRedirectCreatreUrlTree(
            t,
            this.urlSerializer.parse(t),
            e,
            i
          );
        }
        applyRedirectCreatreUrlTree(e, t, i, r) {
          const s = this.createSegmentGroup(e, t.root, i, r);
          return new er(
            s,
            this.createQueryParams(t.queryParams, this.urlTree.queryParams),
            t.fragment
          );
        }
        createQueryParams(e, t) {
          const i = {};
          return (
            rt(e, (r, s) => {
              if ("string" == typeof r && r.startsWith(":")) {
                const a = r.substring(1);
                i[s] = t[a];
              } else i[s] = r;
            }),
            i
          );
        }
        createSegmentGroup(e, t, i, r) {
          const s = this.createSegments(e, t.segments, i, r);
          let o = {};
          return (
            rt(t.children, (a, l) => {
              o[l] = this.createSegmentGroup(e, a, i, r);
            }),
            new te(s, o)
          );
        }
        createSegments(e, t, i, r) {
          return t.map((s) =>
            s.path.startsWith(":")
              ? this.findPosParam(e, s, r)
              : this.findOrReturn(s, i)
          );
        }
        findPosParam(e, t, i) {
          const r = i[t.path.substring(1)];
          if (!r)
            throw new Error(
              `Cannot redirect to '${e}'. Cannot find '${t.path}'.`
            );
          return r;
        }
        findOrReturn(e, t) {
          let i = 0;
          for (const r of t) {
            if (r.path === e.path) return t.splice(i), r;
            i++;
          }
          return e;
        }
      }
      function cp(n) {
        const e = {};
        for (const i of Object.keys(n.children)) {
          const s = cp(n.children[i]);
          (s.segments.length > 0 || s.hasChildren()) && (e[i] = s);
        }
        return (function _j(n) {
          if (1 === n.numberOfChildren && n.children[Y]) {
            const e = n.children[Y];
            return new te(n.segments.concat(e.segments), e.children);
          }
          return n;
        })(new te(n.segments, e));
      }
      class WE {
        constructor(e) {
          (this.path = e), (this.route = this.path[this.path.length - 1]);
        }
      }
      class vc {
        constructor(e, t) {
          (this.component = e), (this.route = t);
        }
      }
      function vj(n, e, t) {
        const i = n._root;
        return Wo(i, e ? e._root : null, t, [i.value]);
      }
      function bc(n, e, t) {
        const i = (function Cj(n) {
          if (!n) return null;
          for (let e = n.parent; e; e = e.parent) {
            const t = e.routeConfig;
            if (t && t._loadedConfig) return t._loadedConfig;
          }
          return null;
        })(e);
        return (i ? i.module.injector : t).get(n);
      }
      function Wo(
        n,
        e,
        t,
        i,
        r = { canDeactivateChecks: [], canActivateChecks: [] }
      ) {
        const s = ps(e);
        return (
          n.children.forEach((o) => {
            (function wj(
              n,
              e,
              t,
              i,
              r = { canDeactivateChecks: [], canActivateChecks: [] }
            ) {
              const s = n.value,
                o = e ? e.value : null,
                a = t ? t.getContext(n.value.outlet) : null;
              if (o && s.routeConfig === o.routeConfig) {
                const l = (function Dj(n, e, t) {
                  if ("function" == typeof t) return t(n, e);
                  switch (t) {
                    case "pathParamsChange":
                      return !tr(n.url, e.url);
                    case "pathParamsOrQueryParamsChange":
                      return (
                        !tr(n.url, e.url) || !Vn(n.queryParams, e.queryParams)
                      );
                    case "always":
                      return !0;
                    case "paramsOrQueryParamsChange":
                      return !np(n, e) || !Vn(n.queryParams, e.queryParams);
                    default:
                      return !np(n, e);
                  }
                })(o, s, s.routeConfig.runGuardsAndResolvers);
                l
                  ? r.canActivateChecks.push(new WE(i))
                  : ((s.data = o.data), (s._resolvedData = o._resolvedData)),
                  Wo(n, e, s.component ? (a ? a.children : null) : t, i, r),
                  l &&
                    a &&
                    a.outlet &&
                    a.outlet.isActivated &&
                    r.canDeactivateChecks.push(new vc(a.outlet.component, o));
              } else
                o && Ko(e, a, r),
                  r.canActivateChecks.push(new WE(i)),
                  Wo(n, null, s.component ? (a ? a.children : null) : t, i, r);
            })(o, s[o.value.outlet], t, i.concat([o.value]), r),
              delete s[o.value.outlet];
          }),
          rt(s, (o, a) => Ko(o, t.getContext(a), r)),
          r
        );
      }
      function Ko(n, e, t) {
        const i = ps(n),
          r = n.value;
        rt(i, (s, o) => {
          Ko(s, r.component ? (e ? e.children.getContext(o) : null) : e, t);
        }),
          t.canDeactivateChecks.push(
            new vc(
              r.component && e && e.outlet && e.outlet.isActivated
                ? e.outlet.component
                : null,
              r
            )
          );
      }
      class kj {}
      function KE(n) {
        return new fe((e) => e.error(n));
      }
      class Rj {
        constructor(e, t, i, r, s, o) {
          (this.rootComponentType = e),
            (this.config = t),
            (this.urlTree = i),
            (this.url = r),
            (this.paramsInheritanceStrategy = s),
            (this.relativeLinkResolution = o);
        }
        recognize() {
          const e = mc(
              this.urlTree.root,
              [],
              [],
              this.config.filter((o) => void 0 === o.redirectTo),
              this.relativeLinkResolution
            ).segmentGroup,
            t = this.processSegmentGroup(this.config, e, Y);
          if (null === t) return null;
          const i = new hc(
              [],
              Object.freeze({}),
              Object.freeze(Object.assign({}, this.urlTree.queryParams)),
              this.urlTree.fragment,
              {},
              Y,
              this.rootComponentType,
              null,
              this.urlTree.root,
              -1,
              {}
            ),
            r = new ri(i, t),
            s = new kE(this.url, r);
          return this.inheritParamsAndData(s._root), s;
        }
        inheritParamsAndData(e) {
          const t = e.value,
            i = xE(t, this.paramsInheritanceStrategy);
          (t.params = Object.freeze(i.params)),
            (t.data = Object.freeze(i.data)),
            e.children.forEach((r) => this.inheritParamsAndData(r));
        }
        processSegmentGroup(e, t, i) {
          return 0 === t.segments.length && t.hasChildren()
            ? this.processChildren(e, t)
            : this.processSegment(e, t, t.segments, i);
        }
        processChildren(e, t) {
          const i = [];
          for (const s of Object.keys(t.children)) {
            const o = t.children[s],
              a = HE(e, s),
              l = this.processSegmentGroup(a, o, s);
            if (null === l) return null;
            i.push(...l);
          }
          const r = YE(i);
          return (
            (function Pj(n) {
              n.sort((e, t) =>
                e.value.outlet === Y
                  ? -1
                  : t.value.outlet === Y
                  ? 1
                  : e.value.outlet.localeCompare(t.value.outlet)
              );
            })(r),
            r
          );
        }
        processSegment(e, t, i, r) {
          for (const s of e) {
            const o = this.processSegmentAgainstRoute(s, t, i, r);
            if (null !== o) return o;
          }
          return zE(t, i, r) ? [] : null;
        }
        processSegmentAgainstRoute(e, t, i, r) {
          if (e.redirectTo || !$E(e, t, i, r)) return null;
          let s,
            o = [],
            a = [];
          if ("**" === e.path) {
            const f = i.length > 0 ? _E(i).parameters : {};
            s = new hc(
              i,
              f,
              Object.freeze(Object.assign({}, this.urlTree.queryParams)),
              this.urlTree.fragment,
              XE(e),
              sn(e),
              e.component,
              e,
              ZE(t),
              QE(t) + i.length,
              JE(e)
            );
          } else {
            const f = gc(t, e, i);
            if (!f.matched) return null;
            (o = f.consumedSegments),
              (a = i.slice(f.lastChild)),
              (s = new hc(
                o,
                f.parameters,
                Object.freeze(Object.assign({}, this.urlTree.queryParams)),
                this.urlTree.fragment,
                XE(e),
                sn(e),
                e.component,
                e,
                ZE(t),
                QE(t) + o.length,
                JE(e)
              ));
          }
          const l = (function Nj(n) {
              return n.children
                ? n.children
                : n.loadChildren
                ? n._loadedConfig.routes
                : [];
            })(e),
            { segmentGroup: c, slicedSegments: u } = mc(
              t,
              o,
              a,
              l.filter((f) => void 0 === f.redirectTo),
              this.relativeLinkResolution
            );
          if (0 === u.length && c.hasChildren()) {
            const f = this.processChildren(l, c);
            return null === f ? null : [new ri(s, f)];
          }
          if (0 === l.length && 0 === u.length) return [new ri(s, [])];
          const d = sn(e) === r,
            h = this.processSegment(l, c, u, d ? Y : r);
          return null === h ? null : [new ri(s, h)];
        }
      }
      function Lj(n) {
        const e = n.value.routeConfig;
        return e && "" === e.path && void 0 === e.redirectTo;
      }
      function YE(n) {
        const e = [],
          t = new Set();
        for (const i of n) {
          if (!Lj(i)) {
            e.push(i);
            continue;
          }
          const r = e.find((s) => i.value.routeConfig === s.value.routeConfig);
          void 0 !== r ? (r.children.push(...i.children), t.add(r)) : e.push(i);
        }
        for (const i of t) {
          const r = YE(i.children);
          e.push(new ri(i.value, r));
        }
        return e.filter((i) => !t.has(i));
      }
      function ZE(n) {
        let e = n;
        for (; e._sourceSegment; ) e = e._sourceSegment;
        return e;
      }
      function QE(n) {
        let e = n,
          t = e._segmentIndexShift ? e._segmentIndexShift : 0;
        for (; e._sourceSegment; )
          (e = e._sourceSegment),
            (t += e._segmentIndexShift ? e._segmentIndexShift : 0);
        return t - 1;
      }
      function XE(n) {
        return n.data || {};
      }
      function JE(n) {
        return n.resolve || {};
      }
      function up(n) {
        return ni((e) => {
          const t = n(e);
          return t ? et(t).pipe(re(() => e)) : H(e);
        });
      }
      class Gj extends class zj {
        shouldDetach(e) {
          return !1;
        }
        store(e, t) {}
        shouldAttach(e) {
          return !1;
        }
        retrieve(e) {
          return null;
        }
        shouldReuseRoute(e, t) {
          return e.routeConfig === t.routeConfig;
        }
      } {}
      const dp = new T("ROUTES");
      class eM {
        constructor(e, t, i, r) {
          (this.injector = e),
            (this.compiler = t),
            (this.onLoadStartListener = i),
            (this.onLoadEndListener = r);
        }
        load(e, t) {
          if (t._loader$) return t._loader$;
          this.onLoadStartListener && this.onLoadStartListener(t);
          const r = this.loadModuleFactory(t.loadChildren).pipe(
            re((s) => {
              this.onLoadEndListener && this.onLoadEndListener(t);
              const o = s.create(e);
              return new op(
                mE(o.injector.get(dp, void 0, U.Self | U.Optional)).map(lp),
                o
              );
            }),
            Si((s) => {
              throw ((t._loader$ = void 0), s);
            })
          );
          return (
            (t._loader$ = new rB(r, () => new le()).pipe(oE())), t._loader$
          );
        }
        loadModuleFactory(e) {
          return Bn(e()).pipe(
            Ke((t) =>
              t instanceof Iv ? H(t) : et(this.compiler.compileModuleAsync(t))
            )
          );
        }
      }
      class Wj {
        shouldProcessUrl(e) {
          return !0;
        }
        extract(e) {
          return e;
        }
        merge(e, t) {
          return e;
        }
      }
      function Kj(n) {
        throw n;
      }
      function Yj(n, e, t) {
        return e.parse("/");
      }
      function tM(n, e) {
        return H(null);
      }
      const Zj = {
          paths: "exact",
          fragment: "ignored",
          matrixParams: "ignored",
          queryParams: "exact",
        },
        Qj = {
          paths: "subset",
          fragment: "ignored",
          matrixParams: "ignored",
          queryParams: "subset",
        };
      let Bt = (() => {
        class n {
          constructor(t, i, r, s, o, a, l) {
            (this.rootComponentType = t),
              (this.urlSerializer = i),
              (this.rootContexts = r),
              (this.location = s),
              (this.config = l),
              (this.lastSuccessfulNavigation = null),
              (this.currentNavigation = null),
              (this.disposed = !1),
              (this.navigationId = 0),
              (this.currentPageId = 0),
              (this.isNgZoneEnabled = !1),
              (this.events = new le()),
              (this.errorHandler = Kj),
              (this.malformedUriErrorHandler = Yj),
              (this.navigated = !1),
              (this.lastSuccessfulId = -1),
              (this.hooks = {
                beforePreactivation: tM,
                afterPreactivation: tM,
              }),
              (this.urlHandlingStrategy = new Wj()),
              (this.routeReuseStrategy = new Gj()),
              (this.onSameUrlNavigation = "ignore"),
              (this.paramsInheritanceStrategy = "emptyOnly"),
              (this.urlUpdateStrategy = "deferred"),
              (this.relativeLinkResolution = "corrected"),
              (this.canceledNavigationResolution = "replace"),
              (this.ngModule = o.get(Zn)),
              (this.console = o.get(db));
            const d = o.get(ee);
            (this.isNgZoneEnabled = d instanceof ee && ee.isInAngularZone()),
              this.resetConfig(l),
              (this.currentUrlTree = (function DB() {
                return new er(new te([], {}), {}, null);
              })()),
              (this.rawUrlTree = this.currentUrlTree),
              (this.browserUrlTree = this.currentUrlTree),
              (this.configLoader = new eM(
                o,
                a,
                (h) => this.triggerEvent(new dE(h)),
                (h) => this.triggerEvent(new hE(h))
              )),
              (this.routerState = IE(
                this.currentUrlTree,
                this.rootComponentType
              )),
              (this.transitions = new en({
                id: 0,
                targetPageId: 0,
                currentUrlTree: this.currentUrlTree,
                currentRawUrl: this.currentUrlTree,
                extractedUrl: this.urlHandlingStrategy.extract(
                  this.currentUrlTree
                ),
                urlAfterRedirects: this.urlHandlingStrategy.extract(
                  this.currentUrlTree
                ),
                rawUrl: this.currentUrlTree,
                extras: {},
                resolve: null,
                reject: null,
                promise: Promise.resolve(!0),
                source: "imperative",
                restoredState: null,
                currentSnapshot: this.routerState.snapshot,
                targetSnapshot: null,
                currentRouterState: this.routerState,
                targetRouterState: null,
                guards: { canActivateChecks: [], canDeactivateChecks: [] },
                guardsResult: null,
              })),
              (this.navigations = this.setupNavigations(this.transitions)),
              this.processNavigations();
          }
          get browserPageId() {
            var t;
            return null === (t = this.location.getState()) || void 0 === t
              ? void 0
              : t.ɵrouterPageId;
          }
          setupNavigations(t) {
            const i = this.events;
            return t.pipe(
              tn((r) => 0 !== r.id),
              re((r) =>
                Object.assign(Object.assign({}, r), {
                  extractedUrl: this.urlHandlingStrategy.extract(r.rawUrl),
                })
              ),
              ni((r) => {
                let s = !1,
                  o = !1;
                return H(r).pipe(
                  Mt((a) => {
                    this.currentNavigation = {
                      id: a.id,
                      initialUrl: a.currentRawUrl,
                      extractedUrl: a.extractedUrl,
                      trigger: a.source,
                      extras: a.extras,
                      previousNavigation: this.lastSuccessfulNavigation
                        ? Object.assign(
                            Object.assign({}, this.lastSuccessfulNavigation),
                            { previousNavigation: null }
                          )
                        : null,
                    };
                  }),
                  ni((a) => {
                    const l = this.browserUrlTree.toString(),
                      c =
                        !this.navigated ||
                        a.extractedUrl.toString() !== l ||
                        l !== this.currentUrlTree.toString();
                    if (
                      ("reload" === this.onSameUrlNavigation || c) &&
                      this.urlHandlingStrategy.shouldProcessUrl(a.rawUrl)
                    )
                      return (
                        Cc(a.source) && (this.browserUrlTree = a.extractedUrl),
                        H(a).pipe(
                          ni((d) => {
                            const h = this.transitions.getValue();
                            return (
                              i.next(
                                new Yf(
                                  d.id,
                                  this.serializeUrl(d.extractedUrl),
                                  d.source,
                                  d.restoredState
                                )
                              ),
                              h !== this.transitions.getValue()
                                ? wn
                                : Promise.resolve(d)
                            );
                          }),
                          (function yj(n, e, t, i) {
                            return ni((r) =>
                              (function gj(n, e, t, i, r) {
                                return new mj(n, e, t, i, r).apply();
                              })(n, e, t, r.extractedUrl, i).pipe(
                                re((s) =>
                                  Object.assign(Object.assign({}, r), {
                                    urlAfterRedirects: s,
                                  })
                                )
                              )
                            );
                          })(
                            this.ngModule.injector,
                            this.configLoader,
                            this.urlSerializer,
                            this.config
                          ),
                          Mt((d) => {
                            this.currentNavigation = Object.assign(
                              Object.assign({}, this.currentNavigation),
                              { finalUrl: d.urlAfterRedirects }
                            );
                          }),
                          (function Vj(n, e, t, i, r) {
                            return Ke((s) =>
                              (function Fj(
                                n,
                                e,
                                t,
                                i,
                                r = "emptyOnly",
                                s = "legacy"
                              ) {
                                try {
                                  const o = new Rj(
                                    n,
                                    e,
                                    t,
                                    i,
                                    r,
                                    s
                                  ).recognize();
                                  return null === o ? KE(new kj()) : H(o);
                                } catch (o) {
                                  return KE(o);
                                }
                              })(
                                n,
                                e,
                                s.urlAfterRedirects,
                                t(s.urlAfterRedirects),
                                i,
                                r
                              ).pipe(
                                re((o) =>
                                  Object.assign(Object.assign({}, s), {
                                    targetSnapshot: o,
                                  })
                                )
                              )
                            );
                          })(
                            this.rootComponentType,
                            this.config,
                            (d) => this.serializeUrl(d),
                            this.paramsInheritanceStrategy,
                            this.relativeLinkResolution
                          ),
                          Mt((d) => {
                            if ("eager" === this.urlUpdateStrategy) {
                              if (!d.extras.skipLocationChange) {
                                const f = this.urlHandlingStrategy.merge(
                                  d.urlAfterRedirects,
                                  d.rawUrl
                                );
                                this.setBrowserUrl(f, d);
                              }
                              this.browserUrlTree = d.urlAfterRedirects;
                            }
                            const h = new uB(
                              d.id,
                              this.serializeUrl(d.extractedUrl),
                              this.serializeUrl(d.urlAfterRedirects),
                              d.targetSnapshot
                            );
                            i.next(h);
                          })
                        )
                      );
                    if (
                      c &&
                      this.rawUrlTree &&
                      this.urlHandlingStrategy.shouldProcessUrl(this.rawUrlTree)
                    ) {
                      const {
                          id: h,
                          extractedUrl: f,
                          source: p,
                          restoredState: g,
                          extras: y,
                        } = a,
                        v = new Yf(h, this.serializeUrl(f), p, g);
                      i.next(v);
                      const m = IE(f, this.rootComponentType).snapshot;
                      return H(
                        Object.assign(Object.assign({}, a), {
                          targetSnapshot: m,
                          urlAfterRedirects: f,
                          extras: Object.assign(Object.assign({}, y), {
                            skipLocationChange: !1,
                            replaceUrl: !1,
                          }),
                        })
                      );
                    }
                    return (this.rawUrlTree = a.rawUrl), a.resolve(null), wn;
                  }),
                  up((a) => {
                    const {
                      targetSnapshot: l,
                      id: c,
                      extractedUrl: u,
                      rawUrl: d,
                      extras: { skipLocationChange: h, replaceUrl: f },
                    } = a;
                    return this.hooks.beforePreactivation(l, {
                      navigationId: c,
                      appliedUrlTree: u,
                      rawUrlTree: d,
                      skipLocationChange: !!h,
                      replaceUrl: !!f,
                    });
                  }),
                  Mt((a) => {
                    const l = new dB(
                      a.id,
                      this.serializeUrl(a.extractedUrl),
                      this.serializeUrl(a.urlAfterRedirects),
                      a.targetSnapshot
                    );
                    this.triggerEvent(l);
                  }),
                  re((a) =>
                    Object.assign(Object.assign({}, a), {
                      guards: vj(
                        a.targetSnapshot,
                        a.currentSnapshot,
                        this.rootContexts
                      ),
                    })
                  ),
                  (function Ej(n, e) {
                    return Ke((t) => {
                      const {
                        targetSnapshot: i,
                        currentSnapshot: r,
                        guards: {
                          canActivateChecks: s,
                          canDeactivateChecks: o,
                        },
                      } = t;
                      return 0 === o.length && 0 === s.length
                        ? H(
                            Object.assign(Object.assign({}, t), {
                              guardsResult: !0,
                            })
                          )
                        : (function Mj(n, e, t, i) {
                            return et(n).pipe(
                              Ke((r) =>
                                (function xj(n, e, t, i, r) {
                                  const s =
                                    e && e.routeConfig
                                      ? e.routeConfig.canDeactivate
                                      : null;
                                  return s && 0 !== s.length
                                    ? H(
                                        s.map((a) => {
                                          const l = bc(a, e, r);
                                          let c;
                                          if (
                                            (function rj(n) {
                                              return n && Ai(n.canDeactivate);
                                            })(l)
                                          )
                                            c = Bn(l.canDeactivate(n, e, t, i));
                                          else {
                                            if (!Ai(l))
                                              throw new Error(
                                                "Invalid CanDeactivate guard"
                                              );
                                            c = Bn(l(n, e, t, i));
                                          }
                                          return c.pipe(hs());
                                        })
                                      ).pipe(zo())
                                    : H(!0);
                                })(r.component, r.route, t, e, i)
                              ),
                              hs((r) => !0 !== r, !0)
                            );
                          })(o, i, r, n).pipe(
                            Ke((a) =>
                              a &&
                              (function ej(n) {
                                return "boolean" == typeof n;
                              })(a)
                                ? (function Sj(n, e, t, i) {
                                    return et(e).pipe(
                                      ds((r) =>
                                        qf(
                                          (function Tj(n, e) {
                                            return (
                                              null !== n && e && e(new gB(n)),
                                              H(!0)
                                            );
                                          })(r.route.parent, i),
                                          (function Aj(n, e) {
                                            return (
                                              null !== n && e && e(new _B(n)),
                                              H(!0)
                                            );
                                          })(r.route, i),
                                          (function Ij(n, e, t) {
                                            const i = e[e.length - 1],
                                              s = e
                                                .slice(0, e.length - 1)
                                                .reverse()
                                                .map((o) =>
                                                  (function bj(n) {
                                                    const e = n.routeConfig
                                                      ? n.routeConfig
                                                          .canActivateChild
                                                      : null;
                                                    return e && 0 !== e.length
                                                      ? { node: n, guards: e }
                                                      : null;
                                                  })(o)
                                                )
                                                .filter((o) => null !== o)
                                                .map((o) =>
                                                  Wf(() =>
                                                    H(
                                                      o.guards.map((l) => {
                                                        const c = bc(
                                                          l,
                                                          o.node,
                                                          t
                                                        );
                                                        let u;
                                                        if (
                                                          (function ij(n) {
                                                            return (
                                                              n &&
                                                              Ai(
                                                                n.canActivateChild
                                                              )
                                                            );
                                                          })(c)
                                                        )
                                                          u = Bn(
                                                            c.canActivateChild(
                                                              i,
                                                              n
                                                            )
                                                          );
                                                        else {
                                                          if (!Ai(c))
                                                            throw new Error(
                                                              "Invalid CanActivateChild guard"
                                                            );
                                                          u = Bn(c(i, n));
                                                        }
                                                        return u.pipe(hs());
                                                      })
                                                    ).pipe(zo())
                                                  )
                                                );
                                            return H(s).pipe(zo());
                                          })(n, r.path, t),
                                          (function Oj(n, e, t) {
                                            const i = e.routeConfig
                                              ? e.routeConfig.canActivate
                                              : null;
                                            if (!i || 0 === i.length)
                                              return H(!0);
                                            const r = i.map((s) =>
                                              Wf(() => {
                                                const o = bc(s, e, t);
                                                let a;
                                                if (
                                                  (function nj(n) {
                                                    return (
                                                      n && Ai(n.canActivate)
                                                    );
                                                  })(o)
                                                )
                                                  a = Bn(o.canActivate(e, n));
                                                else {
                                                  if (!Ai(o))
                                                    throw new Error(
                                                      "Invalid CanActivate guard"
                                                    );
                                                  a = Bn(o(e, n));
                                                }
                                                return a.pipe(hs());
                                              })
                                            );
                                            return H(r).pipe(zo());
                                          })(n, r.route, t)
                                        )
                                      ),
                                      hs((r) => !0 !== r, !0)
                                    );
                                  })(i, s, n, e)
                                : H(a)
                            ),
                            re((a) =>
                              Object.assign(Object.assign({}, t), {
                                guardsResult: a,
                              })
                            )
                          );
                    });
                  })(this.ngModule.injector, (a) => this.triggerEvent(a)),
                  Mt((a) => {
                    if (nr(a.guardsResult)) {
                      const c = Zf(
                        `Redirecting to "${this.serializeUrl(a.guardsResult)}"`
                      );
                      throw ((c.url = a.guardsResult), c);
                    }
                    const l = new hB(
                      a.id,
                      this.serializeUrl(a.extractedUrl),
                      this.serializeUrl(a.urlAfterRedirects),
                      a.targetSnapshot,
                      !!a.guardsResult
                    );
                    this.triggerEvent(l);
                  }),
                  tn(
                    (a) =>
                      !!a.guardsResult ||
                      (this.restoreHistory(a),
                      this.cancelNavigationTransition(a, ""),
                      !1)
                  ),
                  up((a) => {
                    if (a.guards.canActivateChecks.length)
                      return H(a).pipe(
                        Mt((l) => {
                          const c = new fB(
                            l.id,
                            this.serializeUrl(l.extractedUrl),
                            this.serializeUrl(l.urlAfterRedirects),
                            l.targetSnapshot
                          );
                          this.triggerEvent(c);
                        }),
                        ni((l) => {
                          let c = !1;
                          return H(l).pipe(
                            (function Bj(n, e) {
                              return Ke((t) => {
                                const {
                                  targetSnapshot: i,
                                  guards: { canActivateChecks: r },
                                } = t;
                                if (!r.length) return H(t);
                                let s = 0;
                                return et(r).pipe(
                                  ds((o) =>
                                    (function jj(n, e, t, i) {
                                      return (function Hj(n, e, t, i) {
                                        const r = Object.keys(n);
                                        if (0 === r.length) return H({});
                                        const s = {};
                                        return et(r).pipe(
                                          Ke((o) =>
                                            (function Uj(n, e, t, i) {
                                              const r = bc(n, e, i);
                                              return Bn(
                                                r.resolve
                                                  ? r.resolve(e, t)
                                                  : r(e, t)
                                              );
                                            })(n[o], e, t, i).pipe(
                                              Mt((a) => {
                                                s[o] = a;
                                              })
                                            )
                                          ),
                                          Kf(1),
                                          Ke(() =>
                                            Object.keys(s).length === r.length
                                              ? H(s)
                                              : wn
                                          )
                                        );
                                      })(n._resolve, n, e, i).pipe(
                                        re(
                                          (s) => (
                                            (n._resolvedData = s),
                                            (n.data = Object.assign(
                                              Object.assign({}, n.data),
                                              xE(n, t).resolve
                                            )),
                                            null
                                          )
                                        )
                                      );
                                    })(o.route, i, n, e)
                                  ),
                                  Mt(() => s++),
                                  Kf(1),
                                  Ke((o) => (s === r.length ? H(t) : wn))
                                );
                              });
                            })(
                              this.paramsInheritanceStrategy,
                              this.ngModule.injector
                            ),
                            Mt({
                              next: () => (c = !0),
                              complete: () => {
                                c ||
                                  (this.restoreHistory(l),
                                  this.cancelNavigationTransition(
                                    l,
                                    "At least one route resolver didn't emit any value."
                                  ));
                              },
                            })
                          );
                        }),
                        Mt((l) => {
                          const c = new pB(
                            l.id,
                            this.serializeUrl(l.extractedUrl),
                            this.serializeUrl(l.urlAfterRedirects),
                            l.targetSnapshot
                          );
                          this.triggerEvent(c);
                        })
                      );
                  }),
                  up((a) => {
                    const {
                      targetSnapshot: l,
                      id: c,
                      extractedUrl: u,
                      rawUrl: d,
                      extras: { skipLocationChange: h, replaceUrl: f },
                    } = a;
                    return this.hooks.afterPreactivation(l, {
                      navigationId: c,
                      appliedUrlTree: u,
                      rawUrlTree: d,
                      skipLocationChange: !!h,
                      replaceUrl: !!f,
                    });
                  }),
                  re((a) => {
                    const l = (function HB(n, e, t) {
                      const i = Ho(n, e._root, t ? t._root : void 0);
                      return new OE(i, e);
                    })(
                      this.routeReuseStrategy,
                      a.targetSnapshot,
                      a.currentRouterState
                    );
                    return Object.assign(Object.assign({}, a), {
                      targetRouterState: l,
                    });
                  }),
                  Mt((a) => {
                    (this.currentUrlTree = a.urlAfterRedirects),
                      (this.rawUrlTree = this.urlHandlingStrategy.merge(
                        a.urlAfterRedirects,
                        a.rawUrl
                      )),
                      (this.routerState = a.targetRouterState),
                      "deferred" === this.urlUpdateStrategy &&
                        (a.extras.skipLocationChange ||
                          this.setBrowserUrl(this.rawUrlTree, a),
                        (this.browserUrlTree = a.urlAfterRedirects));
                  }),
                  ((n, e, t) =>
                    re(
                      (i) => (
                        new XB(
                          e,
                          i.targetRouterState,
                          i.currentRouterState,
                          t
                        ).activate(n),
                        i
                      )
                    ))(this.rootContexts, this.routeReuseStrategy, (a) =>
                    this.triggerEvent(a)
                  ),
                  Mt({
                    next() {
                      s = !0;
                    },
                    complete() {
                      s = !0;
                    },
                  }),
                  (function lB(n) {
                    return Fe((e, t) => {
                      try {
                        e.subscribe(t);
                      } finally {
                        t.add(n);
                      }
                    });
                  })(() => {
                    var a;
                    s ||
                      o ||
                      this.cancelNavigationTransition(
                        r,
                        `Navigation ID ${r.id} is not equal to the current navigation id ${this.navigationId}`
                      ),
                      (null === (a = this.currentNavigation) || void 0 === a
                        ? void 0
                        : a.id) === r.id && (this.currentNavigation = null);
                  }),
                  Si((a) => {
                    if (
                      ((o = !0),
                      (function bB(n) {
                        return n && n[pE];
                      })(a))
                    ) {
                      const l = nr(a.url);
                      l || ((this.navigated = !0), this.restoreHistory(r, !0));
                      const c = new uE(
                        r.id,
                        this.serializeUrl(r.extractedUrl),
                        a.message
                      );
                      i.next(c),
                        l
                          ? setTimeout(() => {
                              const u = this.urlHandlingStrategy.merge(
                                  a.url,
                                  this.rawUrlTree
                                ),
                                d = {
                                  skipLocationChange:
                                    r.extras.skipLocationChange,
                                  replaceUrl:
                                    "eager" === this.urlUpdateStrategy ||
                                    Cc(r.source),
                                };
                              this.scheduleNavigation(
                                u,
                                "imperative",
                                null,
                                d,
                                {
                                  resolve: r.resolve,
                                  reject: r.reject,
                                  promise: r.promise,
                                }
                              );
                            }, 0)
                          : r.resolve(!1);
                    } else {
                      this.restoreHistory(r, !0);
                      const l = new cB(
                        r.id,
                        this.serializeUrl(r.extractedUrl),
                        a
                      );
                      i.next(l);
                      try {
                        r.resolve(this.errorHandler(a));
                      } catch (c) {
                        r.reject(c);
                      }
                    }
                    return wn;
                  })
                );
              })
            );
          }
          resetRootComponentType(t) {
            (this.rootComponentType = t),
              (this.routerState.root.component = this.rootComponentType);
          }
          setTransition(t) {
            this.transitions.next(
              Object.assign(Object.assign({}, this.transitions.value), t)
            );
          }
          initialNavigation() {
            this.setUpLocationChangeListener(),
              0 === this.navigationId &&
                this.navigateByUrl(this.location.path(!0), { replaceUrl: !0 });
          }
          setUpLocationChangeListener() {
            this.locationSubscription ||
              (this.locationSubscription = this.location.subscribe((t) => {
                const i = "popstate" === t.type ? "popstate" : "hashchange";
                "popstate" === i &&
                  setTimeout(() => {
                    var r;
                    const s = { replaceUrl: !0 },
                      o = (
                        null === (r = t.state) || void 0 === r
                          ? void 0
                          : r.navigationId
                      )
                        ? t.state
                        : null;
                    if (o) {
                      const l = Object.assign({}, o);
                      delete l.navigationId,
                        delete l.ɵrouterPageId,
                        0 !== Object.keys(l).length && (s.state = l);
                    }
                    const a = this.parseUrl(t.url);
                    this.scheduleNavigation(a, i, o, s);
                  }, 0);
              }));
          }
          get url() {
            return this.serializeUrl(this.currentUrlTree);
          }
          getCurrentNavigation() {
            return this.currentNavigation;
          }
          triggerEvent(t) {
            this.events.next(t);
          }
          resetConfig(t) {
            jE(t),
              (this.config = t.map(lp)),
              (this.navigated = !1),
              (this.lastSuccessfulId = -1);
          }
          ngOnDestroy() {
            this.dispose();
          }
          dispose() {
            this.transitions.complete(),
              this.locationSubscription &&
                (this.locationSubscription.unsubscribe(),
                (this.locationSubscription = void 0)),
              (this.disposed = !0);
          }
          createUrlTree(t, i = {}) {
            const {
                relativeTo: r,
                queryParams: s,
                fragment: o,
                queryParamsHandling: a,
                preserveFragment: l,
              } = i,
              c = r || this.routerState.root,
              u = l ? this.currentUrlTree.fragment : o;
            let d = null;
            switch (a) {
              case "merge":
                d = Object.assign(
                  Object.assign({}, this.currentUrlTree.queryParams),
                  s
                );
                break;
              case "preserve":
                d = this.currentUrlTree.queryParams;
                break;
              default:
                d = s || null;
            }
            return (
              null !== d && (d = this.removeEmptyProps(d)),
              (function zB(n, e, t, i, r) {
                if (0 === t.length) return ip(e.root, e.root, e, i, r);
                const s = (function GB(n) {
                  if ("string" == typeof n[0] && 1 === n.length && "/" === n[0])
                    return new PE(!0, 0, n);
                  let e = 0,
                    t = !1;
                  const i = n.reduce((r, s, o) => {
                    if ("object" == typeof s && null != s) {
                      if (s.outlets) {
                        const a = {};
                        return (
                          rt(s.outlets, (l, c) => {
                            a[c] = "string" == typeof l ? l.split("/") : l;
                          }),
                          [...r, { outlets: a }]
                        );
                      }
                      if (s.segmentPath) return [...r, s.segmentPath];
                    }
                    return "string" != typeof s
                      ? [...r, s]
                      : 0 === o
                      ? (s.split("/").forEach((a, l) => {
                          (0 == l && "." === a) ||
                            (0 == l && "" === a
                              ? (t = !0)
                              : ".." === a
                              ? e++
                              : "" != a && r.push(a));
                        }),
                        r)
                      : [...r, s];
                  }, []);
                  return new PE(t, e, i);
                })(t);
                if (s.toRoot()) return ip(e.root, new te([], {}), e, i, r);
                const o = (function qB(n, e, t) {
                    if (n.isAbsolute) return new rp(e.root, !0, 0);
                    if (-1 === t.snapshot._lastPathIndex) {
                      const s = t.snapshot._urlSegment;
                      return new rp(s, s === e.root, 0);
                    }
                    const i = fc(n.commands[0]) ? 0 : 1;
                    return (function WB(n, e, t) {
                      let i = n,
                        r = e,
                        s = t;
                      for (; s > r; ) {
                        if (((s -= r), (i = i.parent), !i))
                          throw new Error("Invalid number of '../'");
                        r = i.segments.length;
                      }
                      return new rp(i, !1, r - s);
                    })(
                      t.snapshot._urlSegment,
                      t.snapshot._lastPathIndex + i,
                      n.numberOfDoubleDots
                    );
                  })(s, e, n),
                  a = o.processChildren
                    ? pc(o.segmentGroup, o.index, s.commands)
                    : NE(o.segmentGroup, o.index, s.commands);
                return ip(o.segmentGroup, a, e, i, r);
              })(c, this.currentUrlTree, t, d, null != u ? u : null)
            );
          }
          navigateByUrl(t, i = { skipLocationChange: !1 }) {
            const r = nr(t) ? t : this.parseUrl(t),
              s = this.urlHandlingStrategy.merge(r, this.rawUrlTree);
            return this.scheduleNavigation(s, "imperative", null, i);
          }
          navigate(t, i = { skipLocationChange: !1 }) {
            return (
              (function Xj(n) {
                for (let e = 0; e < n.length; e++) {
                  const t = n[e];
                  if (null == t)
                    throw new Error(
                      `The requested path contains ${t} segment at index ${e}`
                    );
                }
              })(t),
              this.navigateByUrl(this.createUrlTree(t, i), i)
            );
          }
          serializeUrl(t) {
            return this.urlSerializer.serialize(t);
          }
          parseUrl(t) {
            let i;
            try {
              i = this.urlSerializer.parse(t);
            } catch (r) {
              i = this.malformedUriErrorHandler(r, this.urlSerializer, t);
            }
            return i;
          }
          isActive(t, i) {
            let r;
            if (
              ((r =
                !0 === i
                  ? Object.assign({}, Zj)
                  : !1 === i
                  ? Object.assign({}, Qj)
                  : i),
              nr(t))
            )
              return vE(this.currentUrlTree, t, r);
            const s = this.parseUrl(t);
            return vE(this.currentUrlTree, s, r);
          }
          removeEmptyProps(t) {
            return Object.keys(t).reduce((i, r) => {
              const s = t[r];
              return null != s && (i[r] = s), i;
            }, {});
          }
          processNavigations() {
            this.navigations.subscribe(
              (t) => {
                (this.navigated = !0),
                  (this.lastSuccessfulId = t.id),
                  (this.currentPageId = t.targetPageId),
                  this.events.next(
                    new Vo(
                      t.id,
                      this.serializeUrl(t.extractedUrl),
                      this.serializeUrl(this.currentUrlTree)
                    )
                  ),
                  (this.lastSuccessfulNavigation = this.currentNavigation),
                  t.resolve(!0);
              },
              (t) => {
                this.console.warn(`Unhandled Navigation Error: ${t}`);
              }
            );
          }
          scheduleNavigation(t, i, r, s, o) {
            var a, l, c;
            if (this.disposed) return Promise.resolve(!1);
            const u = this.transitions.value,
              d = Cc(i) && u && !Cc(u.source),
              h = u.rawUrl.toString() === t.toString(),
              f =
                u.id ===
                (null === (a = this.currentNavigation) || void 0 === a
                  ? void 0
                  : a.id);
            if (d && h && f) return Promise.resolve(!0);
            let g, y, v;
            o
              ? ((g = o.resolve), (y = o.reject), (v = o.promise))
              : (v = new Promise((A, $) => {
                  (g = A), (y = $);
                }));
            const m = ++this.navigationId;
            let w;
            return (
              "computed" === this.canceledNavigationResolution
                ? (0 === this.currentPageId && (r = this.location.getState()),
                  (w =
                    r && r.ɵrouterPageId
                      ? r.ɵrouterPageId
                      : s.replaceUrl || s.skipLocationChange
                      ? null !== (l = this.browserPageId) && void 0 !== l
                        ? l
                        : 0
                      : (null !== (c = this.browserPageId) && void 0 !== c
                          ? c
                          : 0) + 1))
                : (w = 0),
              this.setTransition({
                id: m,
                targetPageId: w,
                source: i,
                restoredState: r,
                currentUrlTree: this.currentUrlTree,
                currentRawUrl: this.rawUrlTree,
                rawUrl: t,
                extras: s,
                resolve: g,
                reject: y,
                promise: v,
                currentSnapshot: this.routerState.snapshot,
                currentRouterState: this.routerState,
              }),
              v.catch((A) => Promise.reject(A))
            );
          }
          setBrowserUrl(t, i) {
            const r = this.urlSerializer.serialize(t),
              s = Object.assign(
                Object.assign({}, i.extras.state),
                this.generateNgRouterState(i.id, i.targetPageId)
              );
            this.location.isCurrentPathEqualTo(r) || i.extras.replaceUrl
              ? this.location.replaceState(r, "", s)
              : this.location.go(r, "", s);
          }
          restoreHistory(t, i = !1) {
            var r, s;
            if ("computed" === this.canceledNavigationResolution) {
              const o = this.currentPageId - t.targetPageId;
              ("popstate" !== t.source &&
                "eager" !== this.urlUpdateStrategy &&
                this.currentUrlTree !==
                  (null === (r = this.currentNavigation) || void 0 === r
                    ? void 0
                    : r.finalUrl)) ||
              0 === o
                ? this.currentUrlTree ===
                    (null === (s = this.currentNavigation) || void 0 === s
                      ? void 0
                      : s.finalUrl) &&
                  0 === o &&
                  (this.resetState(t),
                  (this.browserUrlTree = t.currentUrlTree),
                  this.resetUrlToCurrentUrlTree())
                : this.location.historyGo(o);
            } else
              "replace" === this.canceledNavigationResolution &&
                (i && this.resetState(t), this.resetUrlToCurrentUrlTree());
          }
          resetState(t) {
            (this.routerState = t.currentRouterState),
              (this.currentUrlTree = t.currentUrlTree),
              (this.rawUrlTree = this.urlHandlingStrategy.merge(
                this.currentUrlTree,
                t.rawUrl
              ));
          }
          resetUrlToCurrentUrlTree() {
            this.location.replaceState(
              this.urlSerializer.serialize(this.rawUrlTree),
              "",
              this.generateNgRouterState(
                this.lastSuccessfulId,
                this.currentPageId
              )
            );
          }
          cancelNavigationTransition(t, i) {
            const r = new uE(t.id, this.serializeUrl(t.extractedUrl), i);
            this.triggerEvent(r), t.resolve(!1);
          }
          generateNgRouterState(t, i) {
            return "computed" === this.canceledNavigationResolution
              ? { navigationId: t, ɵrouterPageId: i }
              : { navigationId: t };
          }
        }
        return (
          (n.ɵfac = function (t) {
            $a();
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      function Cc(n) {
        return "imperative" !== n;
      }
      class nM {}
      class iM {
        preload(e, t) {
          return H(null);
        }
      }
      let rM = (() => {
          class n {
            constructor(t, i, r, s) {
              (this.router = t),
                (this.injector = r),
                (this.preloadingStrategy = s),
                (this.loader = new eM(
                  r,
                  i,
                  (l) => t.triggerEvent(new dE(l)),
                  (l) => t.triggerEvent(new hE(l))
                ));
            }
            setUpPreloading() {
              this.subscription = this.router.events
                .pipe(
                  tn((t) => t instanceof Vo),
                  ds(() => this.preload())
                )
                .subscribe(() => {});
            }
            preload() {
              const t = this.injector.get(Zn);
              return this.processRoutes(t, this.router.config);
            }
            ngOnDestroy() {
              this.subscription && this.subscription.unsubscribe();
            }
            processRoutes(t, i) {
              const r = [];
              for (const s of i)
                if (s.loadChildren && !s.canLoad && s._loadedConfig) {
                  const o = s._loadedConfig;
                  r.push(this.processRoutes(o.module, o.routes));
                } else
                  s.loadChildren && !s.canLoad
                    ? r.push(this.preloadConfig(t, s))
                    : s.children && r.push(this.processRoutes(t, s.children));
              return et(r).pipe(
                Ds(),
                re((s) => {})
              );
            }
            preloadConfig(t, i) {
              return this.preloadingStrategy.preload(i, () =>
                (i._loadedConfig
                  ? H(i._loadedConfig)
                  : this.loader.load(t.injector, i)
                ).pipe(
                  Ke(
                    (s) => (
                      (i._loadedConfig = s),
                      this.processRoutes(s.module, s.routes)
                    )
                  )
                )
              );
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(Bt), b(sl), b(Qe), b(nM));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })(),
        pp = (() => {
          class n {
            constructor(t, i, r = {}) {
              (this.router = t),
                (this.viewportScroller = i),
                (this.options = r),
                (this.lastId = 0),
                (this.lastSource = "imperative"),
                (this.restoredId = 0),
                (this.store = {}),
                (r.scrollPositionRestoration =
                  r.scrollPositionRestoration || "disabled"),
                (r.anchorScrolling = r.anchorScrolling || "disabled");
            }
            init() {
              "disabled" !== this.options.scrollPositionRestoration &&
                this.viewportScroller.setHistoryScrollRestoration("manual"),
                (this.routerEventsSubscription = this.createScrollEvents()),
                (this.scrollEventsSubscription = this.consumeScrollEvents());
            }
            createScrollEvents() {
              return this.router.events.subscribe((t) => {
                t instanceof Yf
                  ? ((this.store[this.lastId] =
                      this.viewportScroller.getScrollPosition()),
                    (this.lastSource = t.navigationTrigger),
                    (this.restoredId = t.restoredState
                      ? t.restoredState.navigationId
                      : 0))
                  : t instanceof Vo &&
                    ((this.lastId = t.id),
                    this.scheduleScrollEvent(
                      t,
                      this.router.parseUrl(t.urlAfterRedirects).fragment
                    ));
              });
            }
            consumeScrollEvents() {
              return this.router.events.subscribe((t) => {
                t instanceof fE &&
                  (t.position
                    ? "top" === this.options.scrollPositionRestoration
                      ? this.viewportScroller.scrollToPosition([0, 0])
                      : "enabled" === this.options.scrollPositionRestoration &&
                        this.viewportScroller.scrollToPosition(t.position)
                    : t.anchor && "enabled" === this.options.anchorScrolling
                    ? this.viewportScroller.scrollToAnchor(t.anchor)
                    : "disabled" !== this.options.scrollPositionRestoration &&
                      this.viewportScroller.scrollToPosition([0, 0]));
              });
            }
            scheduleScrollEvent(t, i) {
              this.router.triggerEvent(
                new fE(
                  t,
                  "popstate" === this.lastSource
                    ? this.store[this.restoredId]
                    : null,
                  i
                )
              );
            }
            ngOnDestroy() {
              this.routerEventsSubscription &&
                this.routerEventsSubscription.unsubscribe(),
                this.scrollEventsSubscription &&
                  this.scrollEventsSubscription.unsubscribe();
            }
          }
          return (
            (n.ɵfac = function (t) {
              $a();
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })();
      const ir = new T("ROUTER_CONFIGURATION"),
        sM = new T("ROUTER_FORROOT_GUARD"),
        nH = [
          ll,
          { provide: DE, useClass: EE },
          {
            provide: Bt,
            useFactory: function aH(n, e, t, i, r, s, o = {}, a, l) {
              const c = new Bt(null, n, e, t, i, r, mE(s));
              return (
                a && (c.urlHandlingStrategy = a),
                l && (c.routeReuseStrategy = l),
                (function lH(n, e) {
                  n.errorHandler && (e.errorHandler = n.errorHandler),
                    n.malformedUriErrorHandler &&
                      (e.malformedUriErrorHandler = n.malformedUriErrorHandler),
                    n.onSameUrlNavigation &&
                      (e.onSameUrlNavigation = n.onSameUrlNavigation),
                    n.paramsInheritanceStrategy &&
                      (e.paramsInheritanceStrategy =
                        n.paramsInheritanceStrategy),
                    n.relativeLinkResolution &&
                      (e.relativeLinkResolution = n.relativeLinkResolution),
                    n.urlUpdateStrategy &&
                      (e.urlUpdateStrategy = n.urlUpdateStrategy),
                    n.canceledNavigationResolution &&
                      (e.canceledNavigationResolution =
                        n.canceledNavigationResolution);
                })(o, c),
                o.enableTracing &&
                  c.events.subscribe((u) => {
                    var d, h;
                    null === (d = console.group) ||
                      void 0 === d ||
                      d.call(console, `Router Event: ${u.constructor.name}`),
                      console.log(u.toString()),
                      console.log(u),
                      null === (h = console.groupEnd) ||
                        void 0 === h ||
                        h.call(console);
                  }),
                c
              );
            },
            deps: [
              DE,
              Go,
              ll,
              Qe,
              sl,
              dp,
              ir,
              [class qj {}, new An()],
              [class $j {}, new An()],
            ],
          },
          Go,
          {
            provide: gs,
            useFactory: function cH(n) {
              return n.routerState.root;
            },
            deps: [Bt],
          },
          rM,
          iM,
          class tH {
            preload(e, t) {
              return t().pipe(Si(() => H(null)));
            }
          },
          { provide: ir, useValue: { enableTracing: !1 } },
        ];
      function iH() {
        return new _b("Router", Bt);
      }
      let oM = (() => {
        class n {
          constructor(t, i) {}
          static forRoot(t, i) {
            return {
              ngModule: n,
              providers: [
                nH,
                aM(t),
                {
                  provide: sM,
                  useFactory: oH,
                  deps: [[Bt, new An(), new Er()]],
                },
                { provide: ir, useValue: i || {} },
                {
                  provide: ns,
                  useFactory: sH,
                  deps: [qi, [new js(uh), new An()], ir],
                },
                { provide: pp, useFactory: rH, deps: [Bt, CP, ir] },
                {
                  provide: nM,
                  useExisting:
                    i && i.preloadingStrategy ? i.preloadingStrategy : iM,
                },
                { provide: _b, multi: !0, useFactory: iH },
                [
                  gp,
                  { provide: rl, multi: !0, useFactory: uH, deps: [gp] },
                  { provide: lM, useFactory: dH, deps: [gp] },
                  { provide: ub, multi: !0, useExisting: lM },
                ],
              ],
            };
          }
          static forChild(t) {
            return { ngModule: n, providers: [aM(t)] };
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(sM, 8), b(Bt, 8));
          }),
          (n.ɵmod = he({ type: n })),
          (n.ɵinj = ce({})),
          n
        );
      })();
      function rH(n, e, t) {
        return t.scrollOffset && e.setOffset(t.scrollOffset), new pp(n, e, t);
      }
      function sH(n, e, t = {}) {
        return t.useHash ? new rR(n, e) : new Bb(n, e);
      }
      function oH(n) {
        return "guarded";
      }
      function aM(n) {
        return [
          { provide: PS, multi: !0, useValue: n },
          { provide: dp, multi: !0, useValue: n },
        ];
      }
      let gp = (() => {
        class n {
          constructor(t) {
            (this.injector = t),
              (this.initNavigation = !1),
              (this.destroyed = !1),
              (this.resultOfPreactivationDone = new le());
          }
          appInitializer() {
            return this.injector.get(tR, Promise.resolve(null)).then(() => {
              if (this.destroyed) return Promise.resolve(!0);
              let i = null;
              const r = new Promise((a) => (i = a)),
                s = this.injector.get(Bt),
                o = this.injector.get(ir);
              return (
                "disabled" === o.initialNavigation
                  ? (s.setUpLocationChangeListener(), i(!0))
                  : "enabled" === o.initialNavigation ||
                    "enabledBlocking" === o.initialNavigation
                  ? ((s.hooks.afterPreactivation = () =>
                      this.initNavigation
                        ? H(null)
                        : ((this.initNavigation = !0),
                          i(!0),
                          this.resultOfPreactivationDone)),
                    s.initialNavigation())
                  : i(!0),
                r
              );
            });
          }
          bootstrapListener(t) {
            const i = this.injector.get(ir),
              r = this.injector.get(rM),
              s = this.injector.get(pp),
              o = this.injector.get(Bt),
              a = this.injector.get(es);
            t === a.components[0] &&
              (("enabledNonBlocking" === i.initialNavigation ||
                void 0 === i.initialNavigation) &&
                o.initialNavigation(),
              r.setUpPreloading(),
              s.init(),
              o.resetRootComponentType(a.componentTypes[0]),
              this.resultOfPreactivationDone.next(null),
              this.resultOfPreactivationDone.complete());
          }
          ngOnDestroy() {
            this.destroyed = !0;
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(Qe));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      function uH(n) {
        return n.appInitializer.bind(n);
      }
      function dH(n) {
        return n.bootstrapListener.bind(n);
      }
      const lM = new T("Router Initializer"),
        fH = [];
      let pH = (() => {
        class n {}
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵmod = he({ type: n })),
          (n.ɵinj = ce({ imports: [[oM.forRoot(fH)], oM] })),
          n
        );
      })();
      class cM {}
      class uM {}
      class si {
        constructor(e) {
          (this.normalizedNames = new Map()),
            (this.lazyUpdate = null),
            e
              ? (this.lazyInit =
                  "string" == typeof e
                    ? () => {
                        (this.headers = new Map()),
                          e.split("\n").forEach((t) => {
                            const i = t.indexOf(":");
                            if (i > 0) {
                              const r = t.slice(0, i),
                                s = r.toLowerCase(),
                                o = t.slice(i + 1).trim();
                              this.maybeSetNormalizedName(r, s),
                                this.headers.has(s)
                                  ? this.headers.get(s).push(o)
                                  : this.headers.set(s, [o]);
                            }
                          });
                      }
                    : () => {
                        (this.headers = new Map()),
                          Object.keys(e).forEach((t) => {
                            let i = e[t];
                            const r = t.toLowerCase();
                            "string" == typeof i && (i = [i]),
                              i.length > 0 &&
                                (this.headers.set(r, i),
                                this.maybeSetNormalizedName(t, r));
                          });
                      })
              : (this.headers = new Map());
        }
        has(e) {
          return this.init(), this.headers.has(e.toLowerCase());
        }
        get(e) {
          this.init();
          const t = this.headers.get(e.toLowerCase());
          return t && t.length > 0 ? t[0] : null;
        }
        keys() {
          return this.init(), Array.from(this.normalizedNames.values());
        }
        getAll(e) {
          return this.init(), this.headers.get(e.toLowerCase()) || null;
        }
        append(e, t) {
          return this.clone({ name: e, value: t, op: "a" });
        }
        set(e, t) {
          return this.clone({ name: e, value: t, op: "s" });
        }
        delete(e, t) {
          return this.clone({ name: e, value: t, op: "d" });
        }
        maybeSetNormalizedName(e, t) {
          this.normalizedNames.has(t) || this.normalizedNames.set(t, e);
        }
        init() {
          this.lazyInit &&
            (this.lazyInit instanceof si
              ? this.copyFrom(this.lazyInit)
              : this.lazyInit(),
            (this.lazyInit = null),
            this.lazyUpdate &&
              (this.lazyUpdate.forEach((e) => this.applyUpdate(e)),
              (this.lazyUpdate = null)));
        }
        copyFrom(e) {
          e.init(),
            Array.from(e.headers.keys()).forEach((t) => {
              this.headers.set(t, e.headers.get(t)),
                this.normalizedNames.set(t, e.normalizedNames.get(t));
            });
        }
        clone(e) {
          const t = new si();
          return (
            (t.lazyInit =
              this.lazyInit && this.lazyInit instanceof si
                ? this.lazyInit
                : this),
            (t.lazyUpdate = (this.lazyUpdate || []).concat([e])),
            t
          );
        }
        applyUpdate(e) {
          const t = e.name.toLowerCase();
          switch (e.op) {
            case "a":
            case "s":
              let i = e.value;
              if (("string" == typeof i && (i = [i]), 0 === i.length)) return;
              this.maybeSetNormalizedName(e.name, t);
              const r = ("a" === e.op ? this.headers.get(t) : void 0) || [];
              r.push(...i), this.headers.set(t, r);
              break;
            case "d":
              const s = e.value;
              if (s) {
                let o = this.headers.get(t);
                if (!o) return;
                (o = o.filter((a) => -1 === s.indexOf(a))),
                  0 === o.length
                    ? (this.headers.delete(t), this.normalizedNames.delete(t))
                    : this.headers.set(t, o);
              } else this.headers.delete(t), this.normalizedNames.delete(t);
          }
        }
        forEach(e) {
          this.init(),
            Array.from(this.normalizedNames.keys()).forEach((t) =>
              e(this.normalizedNames.get(t), this.headers.get(t))
            );
        }
      }
      class gH {
        encodeKey(e) {
          return dM(e);
        }
        encodeValue(e) {
          return dM(e);
        }
        decodeKey(e) {
          return decodeURIComponent(e);
        }
        decodeValue(e) {
          return decodeURIComponent(e);
        }
      }
      const _H = /%(\d[a-f0-9])/gi,
        yH = {
          40: "@",
          "3A": ":",
          24: "$",
          "2C": ",",
          "3B": ";",
          "2B": "+",
          "3D": "=",
          "3F": "?",
          "2F": "/",
        };
      function dM(n) {
        return encodeURIComponent(n).replace(_H, (e, t) => {
          var i;
          return null !== (i = yH[t]) && void 0 !== i ? i : e;
        });
      }
      function hM(n) {
        return `${n}`;
      }
      class Ti {
        constructor(e = {}) {
          if (
            ((this.updates = null),
            (this.cloneFrom = null),
            (this.encoder = e.encoder || new gH()),
            e.fromString)
          ) {
            if (e.fromObject)
              throw new Error("Cannot specify both fromString and fromObject.");
            this.map = (function mH(n, e) {
              const t = new Map();
              return (
                n.length > 0 &&
                  n
                    .replace(/^\?/, "")
                    .split("&")
                    .forEach((r) => {
                      const s = r.indexOf("="),
                        [o, a] =
                          -1 == s
                            ? [e.decodeKey(r), ""]
                            : [
                                e.decodeKey(r.slice(0, s)),
                                e.decodeValue(r.slice(s + 1)),
                              ],
                        l = t.get(o) || [];
                      l.push(a), t.set(o, l);
                    }),
                t
              );
            })(e.fromString, this.encoder);
          } else
            e.fromObject
              ? ((this.map = new Map()),
                Object.keys(e.fromObject).forEach((t) => {
                  const i = e.fromObject[t];
                  this.map.set(t, Array.isArray(i) ? i : [i]);
                }))
              : (this.map = null);
        }
        has(e) {
          return this.init(), this.map.has(e);
        }
        get(e) {
          this.init();
          const t = this.map.get(e);
          return t ? t[0] : null;
        }
        getAll(e) {
          return this.init(), this.map.get(e) || null;
        }
        keys() {
          return this.init(), Array.from(this.map.keys());
        }
        append(e, t) {
          return this.clone({ param: e, value: t, op: "a" });
        }
        appendAll(e) {
          const t = [];
          return (
            Object.keys(e).forEach((i) => {
              const r = e[i];
              Array.isArray(r)
                ? r.forEach((s) => {
                    t.push({ param: i, value: s, op: "a" });
                  })
                : t.push({ param: i, value: r, op: "a" });
            }),
            this.clone(t)
          );
        }
        set(e, t) {
          return this.clone({ param: e, value: t, op: "s" });
        }
        delete(e, t) {
          return this.clone({ param: e, value: t, op: "d" });
        }
        toString() {
          return (
            this.init(),
            this.keys()
              .map((e) => {
                const t = this.encoder.encodeKey(e);
                return this.map
                  .get(e)
                  .map((i) => t + "=" + this.encoder.encodeValue(i))
                  .join("&");
              })
              .filter((e) => "" !== e)
              .join("&")
          );
        }
        clone(e) {
          const t = new Ti({ encoder: this.encoder });
          return (
            (t.cloneFrom = this.cloneFrom || this),
            (t.updates = (this.updates || []).concat(e)),
            t
          );
        }
        init() {
          null === this.map && (this.map = new Map()),
            null !== this.cloneFrom &&
              (this.cloneFrom.init(),
              this.cloneFrom
                .keys()
                .forEach((e) => this.map.set(e, this.cloneFrom.map.get(e))),
              this.updates.forEach((e) => {
                switch (e.op) {
                  case "a":
                  case "s":
                    const t =
                      ("a" === e.op ? this.map.get(e.param) : void 0) || [];
                    t.push(hM(e.value)), this.map.set(e.param, t);
                    break;
                  case "d":
                    if (void 0 === e.value) {
                      this.map.delete(e.param);
                      break;
                    }
                    {
                      let i = this.map.get(e.param) || [];
                      const r = i.indexOf(hM(e.value));
                      -1 !== r && i.splice(r, 1),
                        i.length > 0
                          ? this.map.set(e.param, i)
                          : this.map.delete(e.param);
                    }
                }
              }),
              (this.cloneFrom = this.updates = null));
        }
      }
      class vH {
        constructor() {
          this.map = new Map();
        }
        set(e, t) {
          return this.map.set(e, t), this;
        }
        get(e) {
          return (
            this.map.has(e) || this.map.set(e, e.defaultValue()),
            this.map.get(e)
          );
        }
        delete(e) {
          return this.map.delete(e), this;
        }
        has(e) {
          return this.map.has(e);
        }
        keys() {
          return this.map.keys();
        }
      }
      function fM(n) {
        return "undefined" != typeof ArrayBuffer && n instanceof ArrayBuffer;
      }
      function pM(n) {
        return "undefined" != typeof Blob && n instanceof Blob;
      }
      function gM(n) {
        return "undefined" != typeof FormData && n instanceof FormData;
      }
      class Yo {
        constructor(e, t, i, r) {
          let s;
          if (
            ((this.url = t),
            (this.body = null),
            (this.reportProgress = !1),
            (this.withCredentials = !1),
            (this.responseType = "json"),
            (this.method = e.toUpperCase()),
            (function bH(n) {
              switch (n) {
                case "DELETE":
                case "GET":
                case "HEAD":
                case "OPTIONS":
                case "JSONP":
                  return !1;
                default:
                  return !0;
              }
            })(this.method) || r
              ? ((this.body = void 0 !== i ? i : null), (s = r))
              : (s = i),
            s &&
              ((this.reportProgress = !!s.reportProgress),
              (this.withCredentials = !!s.withCredentials),
              s.responseType && (this.responseType = s.responseType),
              s.headers && (this.headers = s.headers),
              s.context && (this.context = s.context),
              s.params && (this.params = s.params)),
            this.headers || (this.headers = new si()),
            this.context || (this.context = new vH()),
            this.params)
          ) {
            const o = this.params.toString();
            if (0 === o.length) this.urlWithParams = t;
            else {
              const a = t.indexOf("?");
              this.urlWithParams =
                t + (-1 === a ? "?" : a < t.length - 1 ? "&" : "") + o;
            }
          } else (this.params = new Ti()), (this.urlWithParams = t);
        }
        serializeBody() {
          return null === this.body
            ? null
            : fM(this.body) ||
              pM(this.body) ||
              gM(this.body) ||
              (function CH(n) {
                return (
                  "undefined" != typeof URLSearchParams &&
                  n instanceof URLSearchParams
                );
              })(this.body) ||
              "string" == typeof this.body
            ? this.body
            : this.body instanceof Ti
            ? this.body.toString()
            : "object" == typeof this.body ||
              "boolean" == typeof this.body ||
              Array.isArray(this.body)
            ? JSON.stringify(this.body)
            : this.body.toString();
        }
        detectContentTypeHeader() {
          return null === this.body || gM(this.body)
            ? null
            : pM(this.body)
            ? this.body.type || null
            : fM(this.body)
            ? null
            : "string" == typeof this.body
            ? "text/plain"
            : this.body instanceof Ti
            ? "application/x-www-form-urlencoded;charset=UTF-8"
            : "object" == typeof this.body ||
              "number" == typeof this.body ||
              "boolean" == typeof this.body
            ? "application/json"
            : null;
        }
        clone(e = {}) {
          var t;
          const i = e.method || this.method,
            r = e.url || this.url,
            s = e.responseType || this.responseType,
            o = void 0 !== e.body ? e.body : this.body,
            a =
              void 0 !== e.withCredentials
                ? e.withCredentials
                : this.withCredentials,
            l =
              void 0 !== e.reportProgress
                ? e.reportProgress
                : this.reportProgress;
          let c = e.headers || this.headers,
            u = e.params || this.params;
          const d = null !== (t = e.context) && void 0 !== t ? t : this.context;
          return (
            void 0 !== e.setHeaders &&
              (c = Object.keys(e.setHeaders).reduce(
                (h, f) => h.set(f, e.setHeaders[f]),
                c
              )),
            e.setParams &&
              (u = Object.keys(e.setParams).reduce(
                (h, f) => h.set(f, e.setParams[f]),
                u
              )),
            new Yo(i, r, o, {
              params: u,
              headers: c,
              context: d,
              reportProgress: l,
              responseType: s,
              withCredentials: a,
            })
          );
        }
      }
      var We = (() => (
        ((We = We || {})[(We.Sent = 0)] = "Sent"),
        (We[(We.UploadProgress = 1)] = "UploadProgress"),
        (We[(We.ResponseHeader = 2)] = "ResponseHeader"),
        (We[(We.DownloadProgress = 3)] = "DownloadProgress"),
        (We[(We.Response = 4)] = "Response"),
        (We[(We.User = 5)] = "User"),
        We
      ))();
      class mp {
        constructor(e, t = 200, i = "OK") {
          (this.headers = e.headers || new si()),
            (this.status = void 0 !== e.status ? e.status : t),
            (this.statusText = e.statusText || i),
            (this.url = e.url || null),
            (this.ok = this.status >= 200 && this.status < 300);
        }
      }
      class _p extends mp {
        constructor(e = {}) {
          super(e), (this.type = We.ResponseHeader);
        }
        clone(e = {}) {
          return new _p({
            headers: e.headers || this.headers,
            status: void 0 !== e.status ? e.status : this.status,
            statusText: e.statusText || this.statusText,
            url: e.url || this.url || void 0,
          });
        }
      }
      class wc extends mp {
        constructor(e = {}) {
          super(e),
            (this.type = We.Response),
            (this.body = void 0 !== e.body ? e.body : null);
        }
        clone(e = {}) {
          return new wc({
            body: void 0 !== e.body ? e.body : this.body,
            headers: e.headers || this.headers,
            status: void 0 !== e.status ? e.status : this.status,
            statusText: e.statusText || this.statusText,
            url: e.url || this.url || void 0,
          });
        }
      }
      class mM extends mp {
        constructor(e) {
          super(e, 0, "Unknown Error"),
            (this.name = "HttpErrorResponse"),
            (this.ok = !1),
            (this.message =
              this.status >= 200 && this.status < 300
                ? `Http failure during parsing for ${e.url || "(unknown url)"}`
                : `Http failure response for ${e.url || "(unknown url)"}: ${
                    e.status
                  } ${e.statusText}`),
            (this.error = e.error || null);
        }
      }
      function yp(n, e) {
        return {
          body: e,
          headers: n.headers,
          context: n.context,
          observe: n.observe,
          params: n.params,
          reportProgress: n.reportProgress,
          responseType: n.responseType,
          withCredentials: n.withCredentials,
        };
      }
      let _M = (() => {
        class n {
          constructor(t) {
            this.handler = t;
          }
          request(t, i, r = {}) {
            let s;
            if (t instanceof Yo) s = t;
            else {
              let l, c;
              (l = r.headers instanceof si ? r.headers : new si(r.headers)),
                r.params &&
                  (c =
                    r.params instanceof Ti
                      ? r.params
                      : new Ti({ fromObject: r.params })),
                (s = new Yo(t, i, void 0 !== r.body ? r.body : null, {
                  headers: l,
                  context: r.context,
                  params: c,
                  reportProgress: r.reportProgress,
                  responseType: r.responseType || "json",
                  withCredentials: r.withCredentials,
                }));
            }
            const o = H(s).pipe(ds((l) => this.handler.handle(l)));
            if (t instanceof Yo || "events" === r.observe) return o;
            const a = o.pipe(tn((l) => l instanceof wc));
            switch (r.observe || "body") {
              case "body":
                switch (s.responseType) {
                  case "arraybuffer":
                    return a.pipe(
                      re((l) => {
                        if (null !== l.body && !(l.body instanceof ArrayBuffer))
                          throw new Error("Response is not an ArrayBuffer.");
                        return l.body;
                      })
                    );
                  case "blob":
                    return a.pipe(
                      re((l) => {
                        if (null !== l.body && !(l.body instanceof Blob))
                          throw new Error("Response is not a Blob.");
                        return l.body;
                      })
                    );
                  case "text":
                    return a.pipe(
                      re((l) => {
                        if (null !== l.body && "string" != typeof l.body)
                          throw new Error("Response is not a string.");
                        return l.body;
                      })
                    );
                  default:
                    return a.pipe(re((l) => l.body));
                }
              case "response":
                return a;
              default:
                throw new Error(
                  `Unreachable: unhandled observe type ${r.observe}}`
                );
            }
          }
          delete(t, i = {}) {
            return this.request("DELETE", t, i);
          }
          get(t, i = {}) {
            return this.request("GET", t, i);
          }
          head(t, i = {}) {
            return this.request("HEAD", t, i);
          }
          jsonp(t, i) {
            return this.request("JSONP", t, {
              params: new Ti().append(i, "JSONP_CALLBACK"),
              observe: "body",
              responseType: "json",
            });
          }
          options(t, i = {}) {
            return this.request("OPTIONS", t, i);
          }
          patch(t, i, r = {}) {
            return this.request("PATCH", t, yp(r, i));
          }
          post(t, i, r = {}) {
            return this.request("POST", t, yp(r, i));
          }
          put(t, i, r = {}) {
            return this.request("PUT", t, yp(r, i));
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(cM));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      class yM {
        constructor(e, t) {
          (this.next = e), (this.interceptor = t);
        }
        handle(e) {
          return this.interceptor.intercept(e, this.next);
        }
      }
      const vM = new T("HTTP_INTERCEPTORS");
      let wH = (() => {
        class n {
          intercept(t, i) {
            return i.handle(t);
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      const DH = /^\)\]\}',?\n/;
      let bM = (() => {
        class n {
          constructor(t) {
            this.xhrFactory = t;
          }
          handle(t) {
            if ("JSONP" === t.method)
              throw new Error(
                "Attempted to construct Jsonp request without HttpClientJsonpModule installed."
              );
            return new fe((i) => {
              const r = this.xhrFactory.build();
              if (
                (r.open(t.method, t.urlWithParams),
                t.withCredentials && (r.withCredentials = !0),
                t.headers.forEach((f, p) => r.setRequestHeader(f, p.join(","))),
                t.headers.has("Accept") ||
                  r.setRequestHeader(
                    "Accept",
                    "application/json, text/plain, */*"
                  ),
                !t.headers.has("Content-Type"))
              ) {
                const f = t.detectContentTypeHeader();
                null !== f && r.setRequestHeader("Content-Type", f);
              }
              if (t.responseType) {
                const f = t.responseType.toLowerCase();
                r.responseType = "json" !== f ? f : "text";
              }
              const s = t.serializeBody();
              let o = null;
              const a = () => {
                  if (null !== o) return o;
                  const f = 1223 === r.status ? 204 : r.status,
                    p = r.statusText || "OK",
                    g = new si(r.getAllResponseHeaders()),
                    y =
                      (function EH(n) {
                        return "responseURL" in n && n.responseURL
                          ? n.responseURL
                          : /^X-Request-URL:/m.test(n.getAllResponseHeaders())
                          ? n.getResponseHeader("X-Request-URL")
                          : null;
                      })(r) || t.url;
                  return (
                    (o = new _p({
                      headers: g,
                      status: f,
                      statusText: p,
                      url: y,
                    })),
                    o
                  );
                },
                l = () => {
                  let { headers: f, status: p, statusText: g, url: y } = a(),
                    v = null;
                  204 !== p &&
                    (v = void 0 === r.response ? r.responseText : r.response),
                    0 === p && (p = v ? 200 : 0);
                  let m = p >= 200 && p < 300;
                  if ("json" === t.responseType && "string" == typeof v) {
                    const w = v;
                    v = v.replace(DH, "");
                    try {
                      v = "" !== v ? JSON.parse(v) : null;
                    } catch (A) {
                      (v = w), m && ((m = !1), (v = { error: A, text: v }));
                    }
                  }
                  m
                    ? (i.next(
                        new wc({
                          body: v,
                          headers: f,
                          status: p,
                          statusText: g,
                          url: y || void 0,
                        })
                      ),
                      i.complete())
                    : i.error(
                        new mM({
                          error: v,
                          headers: f,
                          status: p,
                          statusText: g,
                          url: y || void 0,
                        })
                      );
                },
                c = (f) => {
                  const { url: p } = a(),
                    g = new mM({
                      error: f,
                      status: r.status || 0,
                      statusText: r.statusText || "Unknown Error",
                      url: p || void 0,
                    });
                  i.error(g);
                };
              let u = !1;
              const d = (f) => {
                  u || (i.next(a()), (u = !0));
                  let p = { type: We.DownloadProgress, loaded: f.loaded };
                  f.lengthComputable && (p.total = f.total),
                    "text" === t.responseType &&
                      !!r.responseText &&
                      (p.partialText = r.responseText),
                    i.next(p);
                },
                h = (f) => {
                  let p = { type: We.UploadProgress, loaded: f.loaded };
                  f.lengthComputable && (p.total = f.total), i.next(p);
                };
              return (
                r.addEventListener("load", l),
                r.addEventListener("error", c),
                r.addEventListener("timeout", c),
                r.addEventListener("abort", c),
                t.reportProgress &&
                  (r.addEventListener("progress", d),
                  null !== s &&
                    r.upload &&
                    r.upload.addEventListener("progress", h)),
                r.send(s),
                i.next({ type: We.Sent }),
                () => {
                  r.removeEventListener("error", c),
                    r.removeEventListener("abort", c),
                    r.removeEventListener("load", l),
                    r.removeEventListener("timeout", c),
                    t.reportProgress &&
                      (r.removeEventListener("progress", d),
                      null !== s &&
                        r.upload &&
                        r.upload.removeEventListener("progress", h)),
                    r.readyState !== r.DONE && r.abort();
                }
              );
            });
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(rC));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac })),
          n
        );
      })();
      const vp = new T("XSRF_COOKIE_NAME"),
        bp = new T("XSRF_HEADER_NAME");
      class CM {}
      let MH = (() => {
          class n {
            constructor(t, i, r) {
              (this.doc = t),
                (this.platform = i),
                (this.cookieName = r),
                (this.lastCookieString = ""),
                (this.lastToken = null),
                (this.parseCount = 0);
            }
            getToken() {
              if ("server" === this.platform) return null;
              const t = this.doc.cookie || "";
              return (
                t !== this.lastCookieString &&
                  (this.parseCount++,
                  (this.lastToken = Yb(t, this.cookieName)),
                  (this.lastCookieString = t)),
                this.lastToken
              );
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(ue), b(go), b(vp));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })(),
        Cp = (() => {
          class n {
            constructor(t, i) {
              (this.tokenService = t), (this.headerName = i);
            }
            intercept(t, i) {
              const r = t.url.toLowerCase();
              if (
                "GET" === t.method ||
                "HEAD" === t.method ||
                r.startsWith("http://") ||
                r.startsWith("https://")
              )
                return i.handle(t);
              const s = this.tokenService.getToken();
              return (
                null !== s &&
                  !t.headers.has(this.headerName) &&
                  (t = t.clone({ headers: t.headers.set(this.headerName, s) })),
                i.handle(t)
              );
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(CM), b(bp));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })(),
        SH = (() => {
          class n {
            constructor(t, i) {
              (this.backend = t), (this.injector = i), (this.chain = null);
            }
            handle(t) {
              if (null === this.chain) {
                const i = this.injector.get(vM, []);
                this.chain = i.reduceRight(
                  (r, s) => new yM(r, s),
                  this.backend
                );
              }
              return this.chain.handle(t);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(uM), b(Qe));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })(),
        AH = (() => {
          class n {
            static disable() {
              return {
                ngModule: n,
                providers: [{ provide: Cp, useClass: wH }],
              };
            }
            static withOptions(t = {}) {
              return {
                ngModule: n,
                providers: [
                  t.cookieName ? { provide: vp, useValue: t.cookieName } : [],
                  t.headerName ? { provide: bp, useValue: t.headerName } : [],
                ],
              };
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({
              providers: [
                Cp,
                { provide: vM, useExisting: Cp, multi: !0 },
                { provide: CM, useClass: MH },
                { provide: vp, useValue: "XSRF-TOKEN" },
                { provide: bp, useValue: "X-XSRF-TOKEN" },
              ],
            })),
            n
          );
        })(),
        TH = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({
              providers: [
                _M,
                { provide: cM, useClass: SH },
                bM,
                { provide: uM, useExisting: bM },
              ],
              imports: [
                [
                  AH.withOptions({
                    cookieName: "XSRF-TOKEN",
                    headerName: "X-XSRF-TOKEN",
                  }),
                ],
              ],
            })),
            n
          );
        })(),
        OH = (() => {
          class n {
            constructor() {}
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
            n
          );
        })(),
        wM = (() => {
          class n {
            create(t) {
              return "undefined" == typeof MutationObserver
                ? null
                : new MutationObserver(t);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
            n
          );
        })(),
        IH = (() => {
          class n {
            constructor(t) {
              (this._mutationObserverFactory = t),
                (this._observedElements = new Map());
            }
            ngOnDestroy() {
              this._observedElements.forEach((t, i) =>
                this._cleanupObserver(i)
              );
            }
            observe(t) {
              const i = ei(t);
              return new fe((r) => {
                const o = this._observeElement(i).subscribe(r);
                return () => {
                  o.unsubscribe(), this._unobserveElement(i);
                };
              });
            }
            _observeElement(t) {
              if (this._observedElements.has(t))
                this._observedElements.get(t).count++;
              else {
                const i = new le(),
                  r = this._mutationObserverFactory.create((s) => i.next(s));
                r &&
                  r.observe(t, {
                    characterData: !0,
                    childList: !0,
                    subtree: !0,
                  }),
                  this._observedElements.set(t, {
                    observer: r,
                    stream: i,
                    count: 1,
                  });
              }
              return this._observedElements.get(t).stream;
            }
            _unobserveElement(t) {
              this._observedElements.has(t) &&
                (this._observedElements.get(t).count--,
                this._observedElements.get(t).count ||
                  this._cleanupObserver(t));
            }
            _cleanupObserver(t) {
              if (this._observedElements.has(t)) {
                const { observer: i, stream: r } =
                  this._observedElements.get(t);
                i && i.disconnect(),
                  r.complete(),
                  this._observedElements.delete(t);
              }
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(wM));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
            n
          );
        })(),
        xH = (() => {
          class n {
            constructor(t, i, r) {
              (this._contentObserver = t),
                (this._elementRef = i),
                (this._ngZone = r),
                (this.event = new Q()),
                (this._disabled = !1),
                (this._currentSubscription = null);
            }
            get disabled() {
              return this._disabled;
            }
            set disabled(t) {
              (this._disabled = je(t)),
                this._disabled ? this._unsubscribe() : this._subscribe();
            }
            get debounce() {
              return this._debounce;
            }
            set debounce(t) {
              (this._debounce = Oh(t)), this._subscribe();
            }
            ngAfterContentInit() {
              !this._currentSubscription && !this.disabled && this._subscribe();
            }
            ngOnDestroy() {
              this._unsubscribe();
            }
            _subscribe() {
              this._unsubscribe();
              const t = this._contentObserver.observe(this._elementRef);
              this._ngZone.runOutsideAngular(() => {
                this._currentSubscription = (
                  this.debounce ? t.pipe(Rw(this.debounce)) : t
                ).subscribe(this.event);
              });
            }
            _unsubscribe() {
              var t;
              null === (t = this._currentSubscription) ||
                void 0 === t ||
                t.unsubscribe();
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(IH), _(Se), _(ee));
            }),
            (n.ɵdir = x({
              type: n,
              selectors: [["", "cdkObserveContent", ""]],
              inputs: {
                disabled: ["cdkObserveContentDisabled", "disabled"],
                debounce: "debounce",
              },
              outputs: { event: "cdkObserveContent" },
              exportAs: ["cdkObserveContent"],
            })),
            n
          );
        })(),
        kH = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({ providers: [wM] })),
            n
          );
        })();
      const FH = ["addListener", "removeListener"],
        RH = ["addEventListener", "removeEventListener"],
        PH = ["on", "off"];
      function Dc(n, e, t, i) {
        if ((ae(t) && ((i = t), (t = void 0)), i))
          return Dc(n, e, t).pipe(Ih(i));
        const [r, s] = (function VH(n) {
          return ae(n.addEventListener) && ae(n.removeEventListener);
        })(n)
          ? RH.map((o) => (a) => n[o](e, a, t))
          : (function NH(n) {
              return ae(n.addListener) && ae(n.removeListener);
            })(n)
          ? FH.map(DM(n, e))
          : (function LH(n) {
              return ae(n.on) && ae(n.off);
            })(n)
          ? PH.map(DM(n, e))
          : [];
        if (!r && Lc(n)) return Ke((o) => Dc(o, e, t))(St(n));
        if (!r) throw new TypeError("Invalid event target");
        return new fe((o) => {
          const a = (...l) => o.next(1 < l.length ? l : l[0]);
          return r(a), () => s(a);
        });
      }
      function DM(n, e) {
        return (t) => (i) => n[t](e, i);
      }
      const BH = ["connectionContainer"],
        jH = ["inputContainer"],
        HH = ["label"];
      function UH(n, e) {
        1 & n &&
          (za(0),
          D(1, "div", 14),
          Me(2, "div", 15),
          Me(3, "div", 16),
          Me(4, "div", 17),
          E(),
          D(5, "div", 18),
          Me(6, "div", 15),
          Me(7, "div", 16),
          Me(8, "div", 17),
          E(),
          Ga());
      }
      function $H(n, e) {
        if (1 & n) {
          const t = _i();
          D(0, "div", 19),
            Z("cdkObserveContent", function () {
              return nt(t), K().updateOutlineGap();
            }),
            Rt(1, 1),
            E();
        }
        2 & n && F("cdkObserveContentDisabled", "outline" != K().appearance);
      }
      function zH(n, e) {
        if (
          (1 & n && (za(0), Rt(1, 2), D(2, "span"), J(3), E(), Ga()), 2 & n)
        ) {
          const t = K(2);
          k(3), Pt(t._control.placeholder);
        }
      }
      function GH(n, e) {
        1 & n && Rt(0, 3, ["*ngSwitchCase", "true"]);
      }
      function qH(n, e) {
        1 & n && (D(0, "span", 23), J(1, " *"), E());
      }
      function WH(n, e) {
        if (1 & n) {
          const t = _i();
          D(0, "label", 20, 21),
            Z("cdkObserveContent", function () {
              return nt(t), K().updateOutlineGap();
            }),
            be(2, zH, 4, 1, "ng-container", 12),
            be(3, GH, 1, 0, "ng-content", 12),
            be(4, qH, 2, 0, "span", 22),
            E();
        }
        if (2 & n) {
          const t = K();
          Dt("mat-empty", t._control.empty && !t._shouldAlwaysFloat())(
            "mat-form-field-empty",
            t._control.empty && !t._shouldAlwaysFloat()
          )("mat-accent", "accent" == t.color)("mat-warn", "warn" == t.color),
            F("cdkObserveContentDisabled", "outline" != t.appearance)(
              "id",
              t._labelId
            )("ngSwitch", t._hasLabel()),
            $e("for", t._control.id)("aria-owns", t._control.id),
            k(2),
            F("ngSwitchCase", !1),
            k(1),
            F("ngSwitchCase", !0),
            k(1),
            F(
              "ngIf",
              !t.hideRequiredMarker &&
                t._control.required &&
                !t._control.disabled
            );
        }
      }
      function KH(n, e) {
        1 & n && (D(0, "div", 24), Rt(1, 4), E());
      }
      function YH(n, e) {
        if ((1 & n && (D(0, "div", 25), Me(1, "span", 26), E()), 2 & n)) {
          const t = K();
          k(1),
            Dt("mat-accent", "accent" == t.color)(
              "mat-warn",
              "warn" == t.color
            );
        }
      }
      function ZH(n, e) {
        1 & n && (D(0, "div"), Rt(1, 5), E()),
          2 & n && F("@transitionMessages", K()._subscriptAnimationState);
      }
      function QH(n, e) {
        if ((1 & n && (D(0, "div", 30), J(1), E()), 2 & n)) {
          const t = K(2);
          F("id", t._hintLabelId), k(1), Pt(t.hintLabel);
        }
      }
      function XH(n, e) {
        if (
          (1 & n &&
            (D(0, "div", 27),
            be(1, QH, 2, 2, "div", 28),
            Rt(2, 6),
            Me(3, "div", 29),
            Rt(4, 7),
            E()),
          2 & n)
        ) {
          const t = K();
          F("@transitionMessages", t._subscriptAnimationState),
            k(1),
            F("ngIf", t.hintLabel);
        }
      }
      const JH = [
          "*",
          [["", "matPrefix", ""]],
          [["mat-placeholder"]],
          [["mat-label"]],
          [["", "matSuffix", ""]],
          [["mat-error"]],
          [["mat-hint", 3, "align", "end"]],
          [["mat-hint", "align", "end"]],
        ],
        e2 = [
          "*",
          "[matPrefix]",
          "mat-placeholder",
          "mat-label",
          "[matSuffix]",
          "mat-error",
          "mat-hint:not([align='end'])",
          "mat-hint[align='end']",
        ],
        t2 = new T("MatError"),
        n2 = {
          transitionMessages: hf("transitionMessages", [
            Hl("enter", Di({ opacity: 1, transform: "translateY(0%)" })),
            Ul("void => enter", [
              Di({ opacity: 0, transform: "translateY(-5px)" }),
              ff("300ms cubic-bezier(0.55, 0, 0.55, 0.2)"),
            ]),
          ]),
        };
      let Ec = (() => {
        class n {}
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵdir = x({ type: n })),
          n
        );
      })();
      const r2 = new T("MatHint");
      let wp = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵdir = x({ type: n, selectors: [["mat-label"]] })),
            n
          );
        })(),
        s2 = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵdir = x({ type: n, selectors: [["mat-placeholder"]] })),
            n
          );
        })();
      const o2 = new T("MatPrefix"),
        a2 = new T("MatSuffix");
      let EM = 0;
      const c2 = PV(
          class {
            constructor(n) {
              this._elementRef = n;
            }
          },
          "primary"
        ),
        u2 = new T("MAT_FORM_FIELD_DEFAULT_OPTIONS"),
        Dp = new T("MatFormField");
      let d2 = (() => {
          class n extends c2 {
            constructor(t, i, r, s, o, a, l) {
              super(t),
                (this._changeDetectorRef = i),
                (this._dir = r),
                (this._defaults = s),
                (this._platform = o),
                (this._ngZone = a),
                (this._outlineGapCalculationNeededImmediately = !1),
                (this._outlineGapCalculationNeededOnStable = !1),
                (this._destroyed = new le()),
                (this._showAlwaysAnimate = !1),
                (this._subscriptAnimationState = ""),
                (this._hintLabel = ""),
                (this._hintLabelId = "mat-hint-" + EM++),
                (this._labelId = "mat-form-field-label-" + EM++),
                (this.floatLabel = this._getDefaultFloatLabelState()),
                (this._animationsEnabled = "NoopAnimations" !== l),
                (this.appearance = s && s.appearance ? s.appearance : "legacy"),
                (this._hideRequiredMarker =
                  !(!s || null == s.hideRequiredMarker) &&
                  s.hideRequiredMarker);
            }
            get appearance() {
              return this._appearance;
            }
            set appearance(t) {
              const i = this._appearance;
              (this._appearance =
                t || (this._defaults && this._defaults.appearance) || "legacy"),
                "outline" === this._appearance &&
                  i !== t &&
                  (this._outlineGapCalculationNeededOnStable = !0);
            }
            get hideRequiredMarker() {
              return this._hideRequiredMarker;
            }
            set hideRequiredMarker(t) {
              this._hideRequiredMarker = je(t);
            }
            _shouldAlwaysFloat() {
              return "always" === this.floatLabel && !this._showAlwaysAnimate;
            }
            _canLabelFloat() {
              return "never" !== this.floatLabel;
            }
            get hintLabel() {
              return this._hintLabel;
            }
            set hintLabel(t) {
              (this._hintLabel = t), this._processHints();
            }
            get floatLabel() {
              return "legacy" !== this.appearance &&
                "never" === this._floatLabel
                ? "auto"
                : this._floatLabel;
            }
            set floatLabel(t) {
              t !== this._floatLabel &&
                ((this._floatLabel = t || this._getDefaultFloatLabelState()),
                this._changeDetectorRef.markForCheck());
            }
            get _control() {
              return (
                this._explicitFormFieldControl ||
                this._controlNonStatic ||
                this._controlStatic
              );
            }
            set _control(t) {
              this._explicitFormFieldControl = t;
            }
            getLabelId() {
              return this._hasFloatingLabel() ? this._labelId : null;
            }
            getConnectedOverlayOrigin() {
              return this._connectionContainerRef || this._elementRef;
            }
            ngAfterContentInit() {
              this._validateControlChild();
              const t = this._control;
              t.controlType &&
                this._elementRef.nativeElement.classList.add(
                  `mat-form-field-type-${t.controlType}`
                ),
                t.stateChanges.pipe(us(null)).subscribe(() => {
                  this._validatePlaceholders(),
                    this._syncDescribedByIds(),
                    this._changeDetectorRef.markForCheck();
                }),
                t.ngControl &&
                  t.ngControl.valueChanges &&
                  t.ngControl.valueChanges
                    .pipe(Nt(this._destroyed))
                    .subscribe(() => this._changeDetectorRef.markForCheck()),
                this._ngZone.runOutsideAngular(() => {
                  this._ngZone.onStable
                    .pipe(Nt(this._destroyed))
                    .subscribe(() => {
                      this._outlineGapCalculationNeededOnStable &&
                        this.updateOutlineGap();
                    });
                }),
                lr(
                  this._prefixChildren.changes,
                  this._suffixChildren.changes
                ).subscribe(() => {
                  (this._outlineGapCalculationNeededOnStable = !0),
                    this._changeDetectorRef.markForCheck();
                }),
                this._hintChildren.changes.pipe(us(null)).subscribe(() => {
                  this._processHints(), this._changeDetectorRef.markForCheck();
                }),
                this._errorChildren.changes.pipe(us(null)).subscribe(() => {
                  this._syncDescribedByIds(),
                    this._changeDetectorRef.markForCheck();
                }),
                this._dir &&
                  this._dir.change.pipe(Nt(this._destroyed)).subscribe(() => {
                    "function" == typeof requestAnimationFrame
                      ? this._ngZone.runOutsideAngular(() => {
                          requestAnimationFrame(() => this.updateOutlineGap());
                        })
                      : this.updateOutlineGap();
                  });
            }
            ngAfterContentChecked() {
              this._validateControlChild(),
                this._outlineGapCalculationNeededImmediately &&
                  this.updateOutlineGap();
            }
            ngAfterViewInit() {
              (this._subscriptAnimationState = "enter"),
                this._changeDetectorRef.detectChanges();
            }
            ngOnDestroy() {
              this._destroyed.next(), this._destroyed.complete();
            }
            _shouldForward(t) {
              const i = this._control ? this._control.ngControl : null;
              return i && i[t];
            }
            _hasPlaceholder() {
              return !!(
                (this._control && this._control.placeholder) ||
                this._placeholderChild
              );
            }
            _hasLabel() {
              return !(!this._labelChildNonStatic && !this._labelChildStatic);
            }
            _shouldLabelFloat() {
              return (
                this._canLabelFloat() &&
                ((this._control && this._control.shouldLabelFloat) ||
                  this._shouldAlwaysFloat())
              );
            }
            _hideControlPlaceholder() {
              return (
                ("legacy" === this.appearance && !this._hasLabel()) ||
                (this._hasLabel() && !this._shouldLabelFloat())
              );
            }
            _hasFloatingLabel() {
              return (
                this._hasLabel() ||
                ("legacy" === this.appearance && this._hasPlaceholder())
              );
            }
            _getDisplayedMessages() {
              return this._errorChildren &&
                this._errorChildren.length > 0 &&
                this._control.errorState
                ? "error"
                : "hint";
            }
            _animateAndLockLabel() {
              this._hasFloatingLabel() &&
                this._canLabelFloat() &&
                (this._animationsEnabled &&
                  this._label &&
                  ((this._showAlwaysAnimate = !0),
                  Dc(this._label.nativeElement, "transitionend")
                    .pipe(Un(1))
                    .subscribe(() => {
                      this._showAlwaysAnimate = !1;
                    })),
                (this.floatLabel = "always"),
                this._changeDetectorRef.markForCheck());
            }
            _validatePlaceholders() {}
            _processHints() {
              this._validateHints(), this._syncDescribedByIds();
            }
            _validateHints() {}
            _getDefaultFloatLabelState() {
              return (this._defaults && this._defaults.floatLabel) || "auto";
            }
            _syncDescribedByIds() {
              if (this._control) {
                let t = [];
                if (
                  (this._control.userAriaDescribedBy &&
                    "string" == typeof this._control.userAriaDescribedBy &&
                    t.push(...this._control.userAriaDescribedBy.split(" ")),
                  "hint" === this._getDisplayedMessages())
                ) {
                  const i = this._hintChildren
                      ? this._hintChildren.find((s) => "start" === s.align)
                      : null,
                    r = this._hintChildren
                      ? this._hintChildren.find((s) => "end" === s.align)
                      : null;
                  i
                    ? t.push(i.id)
                    : this._hintLabel && t.push(this._hintLabelId),
                    r && t.push(r.id);
                } else
                  this._errorChildren &&
                    t.push(...this._errorChildren.map((i) => i.id));
                this._control.setDescribedByIds(t);
              }
            }
            _validateControlChild() {}
            updateOutlineGap() {
              const t = this._label ? this._label.nativeElement : null,
                i = this._connectionContainerRef.nativeElement,
                r = ".mat-form-field-outline-start",
                s = ".mat-form-field-outline-gap";
              if ("outline" !== this.appearance || !this._platform.isBrowser)
                return;
              if (!t || !t.children.length || !t.textContent.trim()) {
                const u = i.querySelectorAll(`${r}, ${s}`);
                for (let d = 0; d < u.length; d++) u[d].style.width = "0";
                return;
              }
              if (!this._isAttachedToDOM())
                return void (this._outlineGapCalculationNeededImmediately = !0);
              let o = 0,
                a = 0;
              const l = i.querySelectorAll(r),
                c = i.querySelectorAll(s);
              if (this._label && this._label.nativeElement.children.length) {
                const u = i.getBoundingClientRect();
                if (0 === u.width && 0 === u.height)
                  return (
                    (this._outlineGapCalculationNeededOnStable = !0),
                    void (this._outlineGapCalculationNeededImmediately = !1)
                  );
                const d = this._getStartEnd(u),
                  h = t.children,
                  f = this._getStartEnd(h[0].getBoundingClientRect());
                let p = 0;
                for (let g = 0; g < h.length; g++) p += h[g].offsetWidth;
                (o = Math.abs(f - d) - 5), (a = p > 0 ? 0.75 * p + 10 : 0);
              }
              for (let u = 0; u < l.length; u++) l[u].style.width = `${o}px`;
              for (let u = 0; u < c.length; u++) c[u].style.width = `${a}px`;
              this._outlineGapCalculationNeededOnStable =
                this._outlineGapCalculationNeededImmediately = !1;
            }
            _getStartEnd(t) {
              return this._dir && "rtl" === this._dir.value ? t.right : t.left;
            }
            _isAttachedToDOM() {
              const t = this._elementRef.nativeElement;
              if (t.getRootNode) {
                const i = t.getRootNode();
                return i && i !== t;
              }
              return document.documentElement.contains(t);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(
                _(Se),
                _(vi),
                _(Nl, 8),
                _(u2, 8),
                _(Jt),
                _(ee),
                _(No, 8)
              );
            }),
            (n.ɵcmp = Dn({
              type: n,
              selectors: [["mat-form-field"]],
              contentQueries: function (t, i, r) {
                if (
                  (1 & t &&
                    (ut(r, Ec, 5),
                    ut(r, Ec, 7),
                    ut(r, wp, 5),
                    ut(r, wp, 7),
                    ut(r, s2, 5),
                    ut(r, t2, 5),
                    ut(r, r2, 5),
                    ut(r, o2, 5),
                    ut(r, a2, 5)),
                  2 & t)
                ) {
                  let s;
                  Te((s = Oe())) && (i._controlNonStatic = s.first),
                    Te((s = Oe())) && (i._controlStatic = s.first),
                    Te((s = Oe())) && (i._labelChildNonStatic = s.first),
                    Te((s = Oe())) && (i._labelChildStatic = s.first),
                    Te((s = Oe())) && (i._placeholderChild = s.first),
                    Te((s = Oe())) && (i._errorChildren = s),
                    Te((s = Oe())) && (i._hintChildren = s),
                    Te((s = Oe())) && (i._prefixChildren = s),
                    Te((s = Oe())) && (i._suffixChildren = s);
                }
              },
              viewQuery: function (t, i) {
                if ((1 & t && (yi(BH, 7), yi(jH, 5), yi(HH, 5)), 2 & t)) {
                  let r;
                  Te((r = Oe())) && (i._connectionContainerRef = r.first),
                    Te((r = Oe())) && (i._inputContainerRef = r.first),
                    Te((r = Oe())) && (i._label = r.first);
                }
              },
              hostAttrs: [1, "mat-form-field"],
              hostVars: 40,
              hostBindings: function (t, i) {
                2 & t &&
                  Dt(
                    "mat-form-field-appearance-standard",
                    "standard" == i.appearance
                  )("mat-form-field-appearance-fill", "fill" == i.appearance)(
                    "mat-form-field-appearance-outline",
                    "outline" == i.appearance
                  )(
                    "mat-form-field-appearance-legacy",
                    "legacy" == i.appearance
                  )("mat-form-field-invalid", i._control.errorState)(
                    "mat-form-field-can-float",
                    i._canLabelFloat()
                  )("mat-form-field-should-float", i._shouldLabelFloat())(
                    "mat-form-field-has-label",
                    i._hasFloatingLabel()
                  )(
                    "mat-form-field-hide-placeholder",
                    i._hideControlPlaceholder()
                  )("mat-form-field-disabled", i._control.disabled)(
                    "mat-form-field-autofilled",
                    i._control.autofilled
                  )("mat-focused", i._control.focused)(
                    "ng-untouched",
                    i._shouldForward("untouched")
                  )("ng-touched", i._shouldForward("touched"))(
                    "ng-pristine",
                    i._shouldForward("pristine")
                  )("ng-dirty", i._shouldForward("dirty"))(
                    "ng-valid",
                    i._shouldForward("valid")
                  )("ng-invalid", i._shouldForward("invalid"))(
                    "ng-pending",
                    i._shouldForward("pending")
                  )("_mat-animation-noopable", !i._animationsEnabled);
              },
              inputs: {
                color: "color",
                appearance: "appearance",
                hideRequiredMarker: "hideRequiredMarker",
                hintLabel: "hintLabel",
                floatLabel: "floatLabel",
              },
              exportAs: ["matFormField"],
              features: [ge([{ provide: Dp, useExisting: n }]), se],
              ngContentSelectors: e2,
              decls: 15,
              vars: 8,
              consts: [
                [1, "mat-form-field-wrapper"],
                [1, "mat-form-field-flex", 3, "click"],
                ["connectionContainer", ""],
                [4, "ngIf"],
                [
                  "class",
                  "mat-form-field-prefix",
                  3,
                  "cdkObserveContentDisabled",
                  "cdkObserveContent",
                  4,
                  "ngIf",
                ],
                [1, "mat-form-field-infix"],
                ["inputContainer", ""],
                [1, "mat-form-field-label-wrapper"],
                [
                  "class",
                  "mat-form-field-label",
                  3,
                  "cdkObserveContentDisabled",
                  "id",
                  "mat-empty",
                  "mat-form-field-empty",
                  "mat-accent",
                  "mat-warn",
                  "ngSwitch",
                  "cdkObserveContent",
                  4,
                  "ngIf",
                ],
                ["class", "mat-form-field-suffix", 4, "ngIf"],
                ["class", "mat-form-field-underline", 4, "ngIf"],
                [1, "mat-form-field-subscript-wrapper", 3, "ngSwitch"],
                [4, "ngSwitchCase"],
                ["class", "mat-form-field-hint-wrapper", 4, "ngSwitchCase"],
                [1, "mat-form-field-outline"],
                [1, "mat-form-field-outline-start"],
                [1, "mat-form-field-outline-gap"],
                [1, "mat-form-field-outline-end"],
                [1, "mat-form-field-outline", "mat-form-field-outline-thick"],
                [
                  1,
                  "mat-form-field-prefix",
                  3,
                  "cdkObserveContentDisabled",
                  "cdkObserveContent",
                ],
                [
                  1,
                  "mat-form-field-label",
                  3,
                  "cdkObserveContentDisabled",
                  "id",
                  "ngSwitch",
                  "cdkObserveContent",
                ],
                ["label", ""],
                [
                  "class",
                  "mat-placeholder-required mat-form-field-required-marker",
                  "aria-hidden",
                  "true",
                  4,
                  "ngIf",
                ],
                [
                  "aria-hidden",
                  "true",
                  1,
                  "mat-placeholder-required",
                  "mat-form-field-required-marker",
                ],
                [1, "mat-form-field-suffix"],
                [1, "mat-form-field-underline"],
                [1, "mat-form-field-ripple"],
                [1, "mat-form-field-hint-wrapper"],
                ["class", "mat-hint", 3, "id", 4, "ngIf"],
                [1, "mat-form-field-hint-spacer"],
                [1, "mat-hint", 3, "id"],
              ],
              template: function (t, i) {
                1 & t &&
                  (eo(JH),
                  D(0, "div", 0),
                  D(1, "div", 1, 2),
                  Z("click", function (s) {
                    return (
                      i._control.onContainerClick &&
                      i._control.onContainerClick(s)
                    );
                  }),
                  be(3, UH, 9, 0, "ng-container", 3),
                  be(4, $H, 2, 1, "div", 4),
                  D(5, "div", 5, 6),
                  Rt(7),
                  D(8, "span", 7),
                  be(9, WH, 5, 16, "label", 8),
                  E(),
                  E(),
                  be(10, KH, 2, 0, "div", 9),
                  E(),
                  be(11, YH, 2, 4, "div", 10),
                  D(12, "div", 11),
                  be(13, ZH, 2, 1, "div", 12),
                  be(14, XH, 5, 2, "div", 13),
                  E(),
                  E()),
                  2 & t &&
                    (k(3),
                    F("ngIf", "outline" == i.appearance),
                    k(1),
                    F("ngIf", i._prefixChildren.length),
                    k(5),
                    F("ngIf", i._hasFloatingLabel()),
                    k(1),
                    F("ngIf", i._suffixChildren.length),
                    k(1),
                    F("ngIf", "outline" != i.appearance),
                    k(1),
                    F("ngSwitch", i._getDisplayedMessages()),
                    k(1),
                    F("ngSwitchCase", "error"),
                    k(1),
                    F("ngSwitchCase", "hint"));
              },
              directives: [vl, xH, vo, bh],
              styles: [
                ".mat-form-field{display:inline-block;position:relative;text-align:left}[dir=rtl] .mat-form-field{text-align:right}.mat-form-field-wrapper{position:relative}.mat-form-field-flex{display:inline-flex;align-items:baseline;box-sizing:border-box;width:100%}.mat-form-field-prefix,.mat-form-field-suffix{white-space:nowrap;flex:none;position:relative}.mat-form-field-infix{display:block;position:relative;flex:auto;min-width:0;width:180px}.cdk-high-contrast-active .mat-form-field-infix{border-image:linear-gradient(transparent, transparent)}.mat-form-field-label-wrapper{position:absolute;left:0;box-sizing:content-box;width:100%;height:100%;overflow:hidden;pointer-events:none}[dir=rtl] .mat-form-field-label-wrapper{left:auto;right:0}.mat-form-field-label{position:absolute;left:0;font:inherit;pointer-events:none;width:100%;white-space:nowrap;text-overflow:ellipsis;overflow:hidden;transform-origin:0 0;transition:transform 400ms cubic-bezier(0.25, 0.8, 0.25, 1),color 400ms cubic-bezier(0.25, 0.8, 0.25, 1),width 400ms cubic-bezier(0.25, 0.8, 0.25, 1);display:none}[dir=rtl] .mat-form-field-label{transform-origin:100% 0;left:auto;right:0}.cdk-high-contrast-active .mat-form-field-disabled .mat-form-field-label{color:GrayText}.mat-form-field-empty.mat-form-field-label,.mat-form-field-can-float.mat-form-field-should-float .mat-form-field-label{display:block}.mat-form-field-autofill-control:-webkit-autofill+.mat-form-field-label-wrapper .mat-form-field-label{display:none}.mat-form-field-can-float .mat-form-field-autofill-control:-webkit-autofill+.mat-form-field-label-wrapper .mat-form-field-label{display:block;transition:none}.mat-input-server:focus+.mat-form-field-label-wrapper .mat-form-field-label,.mat-input-server[placeholder]:not(:placeholder-shown)+.mat-form-field-label-wrapper .mat-form-field-label{display:none}.mat-form-field-can-float .mat-input-server:focus+.mat-form-field-label-wrapper .mat-form-field-label,.mat-form-field-can-float .mat-input-server[placeholder]:not(:placeholder-shown)+.mat-form-field-label-wrapper .mat-form-field-label{display:block}.mat-form-field-label:not(.mat-form-field-empty){transition:none}.mat-form-field-underline{position:absolute;width:100%;pointer-events:none;transform:scale3d(1, 1.0001, 1)}.mat-form-field-ripple{position:absolute;left:0;width:100%;transform-origin:50%;transform:scaleX(0.5);opacity:0;transition:background-color 300ms cubic-bezier(0.55, 0, 0.55, 0.2)}.mat-form-field.mat-focused .mat-form-field-ripple,.mat-form-field.mat-form-field-invalid .mat-form-field-ripple{opacity:1;transform:none;transition:transform 300ms cubic-bezier(0.25, 0.8, 0.25, 1),opacity 100ms cubic-bezier(0.25, 0.8, 0.25, 1),background-color 300ms cubic-bezier(0.25, 0.8, 0.25, 1)}.mat-form-field-subscript-wrapper{position:absolute;box-sizing:border-box;width:100%;overflow:hidden}.mat-form-field-subscript-wrapper .mat-icon,.mat-form-field-label-wrapper .mat-icon{width:1em;height:1em;font-size:inherit;vertical-align:baseline}.mat-form-field-hint-wrapper{display:flex}.mat-form-field-hint-spacer{flex:1 0 1em}.mat-error{display:block}.mat-form-field-control-wrapper{position:relative}.mat-form-field-hint-end{order:1}.mat-form-field._mat-animation-noopable .mat-form-field-label,.mat-form-field._mat-animation-noopable .mat-form-field-ripple{transition:none}\n",
                '.mat-form-field-appearance-fill .mat-form-field-flex{border-radius:4px 4px 0 0;padding:.75em .75em 0 .75em}.cdk-high-contrast-active .mat-form-field-appearance-fill .mat-form-field-flex{outline:solid 1px}.cdk-high-contrast-active .mat-form-field-appearance-fill.mat-form-field-disabled .mat-form-field-flex{outline-color:GrayText}.cdk-high-contrast-active .mat-form-field-appearance-fill.mat-focused .mat-form-field-flex{outline:dashed 3px}.mat-form-field-appearance-fill .mat-form-field-underline::before{content:"";display:block;position:absolute;bottom:0;height:1px;width:100%}.mat-form-field-appearance-fill .mat-form-field-ripple{bottom:0;height:2px}.cdk-high-contrast-active .mat-form-field-appearance-fill .mat-form-field-ripple{height:0}.mat-form-field-appearance-fill:not(.mat-form-field-disabled) .mat-form-field-flex:hover~.mat-form-field-underline .mat-form-field-ripple{opacity:1;transform:none;transition:opacity 600ms cubic-bezier(0.25, 0.8, 0.25, 1)}.mat-form-field-appearance-fill._mat-animation-noopable:not(.mat-form-field-disabled) .mat-form-field-flex:hover~.mat-form-field-underline .mat-form-field-ripple{transition:none}.mat-form-field-appearance-fill .mat-form-field-subscript-wrapper{padding:0 1em}\n',
                '.mat-input-element{font:inherit;background:transparent;color:currentColor;border:none;outline:none;padding:0;margin:0;width:100%;max-width:100%;vertical-align:bottom;text-align:inherit;box-sizing:content-box}.mat-input-element:-moz-ui-invalid{box-shadow:none}.mat-input-element,.mat-input-element::-webkit-search-cancel-button,.mat-input-element::-webkit-search-decoration,.mat-input-element::-webkit-search-results-button,.mat-input-element::-webkit-search-results-decoration{-webkit-appearance:none}.mat-input-element::-webkit-contacts-auto-fill-button,.mat-input-element::-webkit-caps-lock-indicator,.mat-input-element:not([type=password])::-webkit-credentials-auto-fill-button{visibility:hidden}.mat-input-element[type=date],.mat-input-element[type=datetime],.mat-input-element[type=datetime-local],.mat-input-element[type=month],.mat-input-element[type=week],.mat-input-element[type=time]{line-height:1}.mat-input-element[type=date]::after,.mat-input-element[type=datetime]::after,.mat-input-element[type=datetime-local]::after,.mat-input-element[type=month]::after,.mat-input-element[type=week]::after,.mat-input-element[type=time]::after{content:" ";white-space:pre;width:1px}.mat-input-element::-webkit-inner-spin-button,.mat-input-element::-webkit-calendar-picker-indicator,.mat-input-element::-webkit-clear-button{font-size:.75em}.mat-input-element::placeholder{-webkit-user-select:none;user-select:none;transition:color 400ms 133.3333333333ms cubic-bezier(0.25, 0.8, 0.25, 1)}.mat-input-element::-moz-placeholder{-webkit-user-select:none;user-select:none;transition:color 400ms 133.3333333333ms cubic-bezier(0.25, 0.8, 0.25, 1)}.mat-input-element::-webkit-input-placeholder{-webkit-user-select:none;user-select:none;transition:color 400ms 133.3333333333ms cubic-bezier(0.25, 0.8, 0.25, 1)}.mat-input-element:-ms-input-placeholder{-webkit-user-select:none;user-select:none;transition:color 400ms 133.3333333333ms cubic-bezier(0.25, 0.8, 0.25, 1)}.mat-form-field-hide-placeholder .mat-input-element::placeholder{color:transparent !important;-webkit-text-fill-color:transparent;transition:none}.cdk-high-contrast-active .mat-form-field-hide-placeholder .mat-input-element::placeholder{opacity:0}.mat-form-field-hide-placeholder .mat-input-element::-moz-placeholder{color:transparent !important;-webkit-text-fill-color:transparent;transition:none}.cdk-high-contrast-active .mat-form-field-hide-placeholder .mat-input-element::-moz-placeholder{opacity:0}.mat-form-field-hide-placeholder .mat-input-element::-webkit-input-placeholder{color:transparent !important;-webkit-text-fill-color:transparent;transition:none}.cdk-high-contrast-active .mat-form-field-hide-placeholder .mat-input-element::-webkit-input-placeholder{opacity:0}.mat-form-field-hide-placeholder .mat-input-element:-ms-input-placeholder{color:transparent !important;-webkit-text-fill-color:transparent;transition:none}.cdk-high-contrast-active .mat-form-field-hide-placeholder .mat-input-element:-ms-input-placeholder{opacity:0}textarea.mat-input-element{resize:vertical;overflow:auto}textarea.mat-input-element.cdk-textarea-autosize{resize:none}textarea.mat-input-element{padding:2px 0;margin:-2px 0}select.mat-input-element{-moz-appearance:none;-webkit-appearance:none;position:relative;background-color:transparent;display:inline-flex;box-sizing:border-box;padding-top:1em;top:-1em;margin-bottom:-1em}select.mat-input-element::-moz-focus-inner{border:0}select.mat-input-element:not(:disabled){cursor:pointer}.mat-form-field-type-mat-native-select .mat-form-field-infix::after{content:"";width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:5px solid;position:absolute;top:50%;right:0;margin-top:-2.5px;pointer-events:none}[dir=rtl] .mat-form-field-type-mat-native-select .mat-form-field-infix::after{right:auto;left:0}.mat-form-field-type-mat-native-select .mat-input-element{padding-right:15px}[dir=rtl] .mat-form-field-type-mat-native-select .mat-input-element{padding-right:0;padding-left:15px}.mat-form-field-type-mat-native-select .mat-form-field-label-wrapper{max-width:calc(100% - 10px)}.mat-form-field-type-mat-native-select.mat-form-field-appearance-outline .mat-form-field-infix::after{margin-top:-5px}.mat-form-field-type-mat-native-select.mat-form-field-appearance-fill .mat-form-field-infix::after{margin-top:-10px}\n',
                ".mat-form-field-appearance-legacy .mat-form-field-label{transform:perspective(100px)}.mat-form-field-appearance-legacy .mat-form-field-prefix .mat-icon,.mat-form-field-appearance-legacy .mat-form-field-suffix .mat-icon{width:1em}.mat-form-field-appearance-legacy .mat-form-field-prefix .mat-icon-button,.mat-form-field-appearance-legacy .mat-form-field-suffix .mat-icon-button{font:inherit;vertical-align:baseline}.mat-form-field-appearance-legacy .mat-form-field-prefix .mat-icon-button .mat-icon,.mat-form-field-appearance-legacy .mat-form-field-suffix .mat-icon-button .mat-icon{font-size:inherit}.mat-form-field-appearance-legacy .mat-form-field-underline{height:1px}.cdk-high-contrast-active .mat-form-field-appearance-legacy .mat-form-field-underline{height:0;border-top:solid 1px}.mat-form-field-appearance-legacy .mat-form-field-ripple{top:0;height:2px;overflow:hidden}.cdk-high-contrast-active .mat-form-field-appearance-legacy .mat-form-field-ripple{height:0;border-top:solid 2px}.mat-form-field-appearance-legacy.mat-form-field-disabled .mat-form-field-underline{background-position:0;background-color:transparent}.cdk-high-contrast-active .mat-form-field-appearance-legacy.mat-form-field-disabled .mat-form-field-underline{border-top-style:dotted;border-top-width:2px;border-top-color:GrayText}.mat-form-field-appearance-legacy.mat-form-field-invalid:not(.mat-focused) .mat-form-field-ripple{height:1px}\n",
                ".mat-form-field-appearance-outline .mat-form-field-wrapper{margin:.25em 0}.mat-form-field-appearance-outline .mat-form-field-flex{padding:0 .75em 0 .75em;margin-top:-0.25em;position:relative}.mat-form-field-appearance-outline .mat-form-field-prefix,.mat-form-field-appearance-outline .mat-form-field-suffix{top:.25em}.mat-form-field-appearance-outline .mat-form-field-outline{display:flex;position:absolute;top:.25em;left:0;right:0;bottom:0;pointer-events:none}.mat-form-field-appearance-outline .mat-form-field-outline-start,.mat-form-field-appearance-outline .mat-form-field-outline-end{border:1px solid currentColor;min-width:5px}.mat-form-field-appearance-outline .mat-form-field-outline-start{border-radius:5px 0 0 5px;border-right-style:none}[dir=rtl] .mat-form-field-appearance-outline .mat-form-field-outline-start{border-right-style:solid;border-left-style:none;border-radius:0 5px 5px 0}.mat-form-field-appearance-outline .mat-form-field-outline-end{border-radius:0 5px 5px 0;border-left-style:none;flex-grow:1}[dir=rtl] .mat-form-field-appearance-outline .mat-form-field-outline-end{border-left-style:solid;border-right-style:none;border-radius:5px 0 0 5px}.mat-form-field-appearance-outline .mat-form-field-outline-gap{border-radius:.000001px;border:1px solid currentColor;border-left-style:none;border-right-style:none}.mat-form-field-appearance-outline.mat-form-field-can-float.mat-form-field-should-float .mat-form-field-outline-gap{border-top-color:transparent}.mat-form-field-appearance-outline .mat-form-field-outline-thick{opacity:0}.mat-form-field-appearance-outline .mat-form-field-outline-thick .mat-form-field-outline-start,.mat-form-field-appearance-outline .mat-form-field-outline-thick .mat-form-field-outline-end,.mat-form-field-appearance-outline .mat-form-field-outline-thick .mat-form-field-outline-gap{border-width:2px}.mat-form-field-appearance-outline.mat-focused .mat-form-field-outline,.mat-form-field-appearance-outline.mat-form-field-invalid .mat-form-field-outline{opacity:0;transition:opacity 100ms cubic-bezier(0.25, 0.8, 0.25, 1)}.mat-form-field-appearance-outline.mat-focused .mat-form-field-outline-thick,.mat-form-field-appearance-outline.mat-form-field-invalid .mat-form-field-outline-thick{opacity:1}.cdk-high-contrast-active .mat-form-field-appearance-outline.mat-focused .mat-form-field-outline-thick{border:3px dashed}.mat-form-field-appearance-outline:not(.mat-form-field-disabled) .mat-form-field-flex:hover .mat-form-field-outline{opacity:0;transition:opacity 600ms cubic-bezier(0.25, 0.8, 0.25, 1)}.mat-form-field-appearance-outline:not(.mat-form-field-disabled) .mat-form-field-flex:hover .mat-form-field-outline-thick{opacity:1}.mat-form-field-appearance-outline .mat-form-field-subscript-wrapper{padding:0 1em}.cdk-high-contrast-active .mat-form-field-appearance-outline.mat-form-field-disabled .mat-form-field-outline{color:GrayText}.mat-form-field-appearance-outline._mat-animation-noopable:not(.mat-form-field-disabled) .mat-form-field-flex:hover~.mat-form-field-outline,.mat-form-field-appearance-outline._mat-animation-noopable .mat-form-field-outline,.mat-form-field-appearance-outline._mat-animation-noopable .mat-form-field-outline-start,.mat-form-field-appearance-outline._mat-animation-noopable .mat-form-field-outline-end,.mat-form-field-appearance-outline._mat-animation-noopable .mat-form-field-outline-gap{transition:none}\n",
                ".mat-form-field-appearance-standard .mat-form-field-flex{padding-top:.75em}.mat-form-field-appearance-standard .mat-form-field-underline{height:1px}.cdk-high-contrast-active .mat-form-field-appearance-standard .mat-form-field-underline{height:0;border-top:solid 1px}.mat-form-field-appearance-standard .mat-form-field-ripple{bottom:0;height:2px}.cdk-high-contrast-active .mat-form-field-appearance-standard .mat-form-field-ripple{height:0;border-top:solid 2px}.mat-form-field-appearance-standard.mat-form-field-disabled .mat-form-field-underline{background-position:0;background-color:transparent}.cdk-high-contrast-active .mat-form-field-appearance-standard.mat-form-field-disabled .mat-form-field-underline{border-top-style:dotted;border-top-width:2px}.mat-form-field-appearance-standard:not(.mat-form-field-disabled) .mat-form-field-flex:hover~.mat-form-field-underline .mat-form-field-ripple{opacity:1;transform:none;transition:opacity 600ms cubic-bezier(0.25, 0.8, 0.25, 1)}.mat-form-field-appearance-standard._mat-animation-noopable:not(.mat-form-field-disabled) .mat-form-field-flex:hover~.mat-form-field-underline .mat-form-field-ripple{transition:none}\n",
              ],
              encapsulation: 2,
              data: { animation: [n2.transitionMessages] },
              changeDetection: 0,
            })),
            n
          );
        })(),
        Mc = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({ imports: [[bl, bn, kH], bn] })),
            n
          );
        })();
      const Zo = {
        schedule(n) {
          let e = requestAnimationFrame,
            t = cancelAnimationFrame;
          const { delegate: i } = Zo;
          i && ((e = i.requestAnimationFrame), (t = i.cancelAnimationFrame));
          const r = e((s) => {
            (t = void 0), n(s);
          });
          return new Le(() => (null == t ? void 0 : t(r)));
        },
        requestAnimationFrame(...n) {
          const { delegate: e } = Zo;
          return (
            (null == e ? void 0 : e.requestAnimationFrame) ||
            requestAnimationFrame
          )(...n);
        },
        cancelAnimationFrame(...n) {
          const { delegate: e } = Zo;
          return (
            (null == e ? void 0 : e.cancelAnimationFrame) ||
            cancelAnimationFrame
          )(...n);
        },
        delegate: void 0,
      };
      new (class f2 extends uf {
        flush(e) {
          (this._active = !0), (this._scheduled = void 0);
          const { actions: t } = this;
          let i,
            r = -1;
          e = e || t.shift();
          const s = t.length;
          do {
            if ((i = e.execute(e.state, e.delay))) break;
          } while (++r < s && (e = t.shift()));
          if (((this._active = !1), i)) {
            for (; ++r < s && (e = t.shift()); ) e.unsubscribe();
            throw i;
          }
        }
      })(
        class h2 extends cf {
          constructor(e, t) {
            super(e, t), (this.scheduler = e), (this.work = t);
          }
          requestAsyncId(e, t, i = 0) {
            return null !== i && i > 0
              ? super.requestAsyncId(e, t, i)
              : (e.actions.push(this),
                e._scheduled ||
                  (e._scheduled = Zo.requestAnimationFrame(() =>
                    e.flush(void 0)
                  )));
          }
          recycleAsyncId(e, t, i = 0) {
            if ((null != i && i > 0) || (null == i && this.delay > 0))
              return super.recycleAsyncId(e, t, i);
            0 === e.actions.length &&
              (Zo.cancelAnimationFrame(t), (e._scheduled = void 0));
          }
        }
      );
      let Ep,
        g2 = 1;
      const Sc = {};
      function SM(n) {
        return n in Sc && (delete Sc[n], !0);
      }
      const m2 = {
          setImmediate(n) {
            const e = g2++;
            return (
              (Sc[e] = !0),
              Ep || (Ep = Promise.resolve()),
              Ep.then(() => SM(e) && n()),
              e
            );
          },
          clearImmediate(n) {
            SM(n);
          },
        },
        { setImmediate: _2, clearImmediate: y2 } = m2,
        Ac = {
          setImmediate(...n) {
            const { delegate: e } = Ac;
            return ((null == e ? void 0 : e.setImmediate) || _2)(...n);
          },
          clearImmediate(n) {
            const { delegate: e } = Ac;
            return ((null == e ? void 0 : e.clearImmediate) || y2)(n);
          },
          delegate: void 0,
        };
      new (class b2 extends uf {
        flush(e) {
          (this._active = !0), (this._scheduled = void 0);
          const { actions: t } = this;
          let i,
            r = -1;
          e = e || t.shift();
          const s = t.length;
          do {
            if ((i = e.execute(e.state, e.delay))) break;
          } while (++r < s && (e = t.shift()));
          if (((this._active = !1), i)) {
            for (; ++r < s && (e = t.shift()); ) e.unsubscribe();
            throw i;
          }
        }
      })(
        class v2 extends cf {
          constructor(e, t) {
            super(e, t), (this.scheduler = e), (this.work = t);
          }
          requestAsyncId(e, t, i = 0) {
            return null !== i && i > 0
              ? super.requestAsyncId(e, t, i)
              : (e.actions.push(this),
                e._scheduled ||
                  (e._scheduled = Ac.setImmediate(e.flush.bind(e, void 0))));
          }
          recycleAsyncId(e, t, i = 0) {
            if ((null != i && i > 0) || (null == i && this.delay > 0))
              return super.recycleAsyncId(e, t, i);
            0 === e.actions.length &&
              (Ac.clearImmediate(t), (e._scheduled = void 0));
          }
        }
      );
      function AM(n, e = Fw) {
        return (function w2(n) {
          return Fe((e, t) => {
            let i = !1,
              r = null,
              s = null,
              o = !1;
            const a = () => {
                if ((null == s || s.unsubscribe(), (s = null), i)) {
                  i = !1;
                  const c = r;
                  (r = null), t.next(c);
                }
                o && t.complete();
              },
              l = () => {
                (s = null), o && t.complete();
              };
            e.subscribe(
              new De(
                t,
                (c) => {
                  (i = !0),
                    (r = c),
                    s || St(n(c)).subscribe((s = new De(t, a, l)));
                },
                () => {
                  (o = !0), (!i || !s || s.closed) && t.complete();
                }
              )
            );
          });
        })(() =>
          (function E2(n = 0, e, t = Fw) {
            let i = -1;
            return (
              null != e && (Qp(e) ? (t = e) : (i = e)),
              new fe((r) => {
                let s = (function D2(n) {
                  return n instanceof Date && !isNaN(n);
                })(n)
                  ? +n - t.now()
                  : n;
                s < 0 && (s = 0);
                let o = 0;
                return t.schedule(function () {
                  r.closed ||
                    (r.next(o++),
                    0 <= i ? this.schedule(void 0, i) : r.complete());
                }, s);
              })
            );
          })(n, e)
        );
      }
      let S2 = (() => {
          class n {
            constructor(t, i, r) {
              (this._ngZone = t),
                (this._platform = i),
                (this._scrolled = new le()),
                (this._globalSubscription = null),
                (this._scrolledCount = 0),
                (this.scrollContainers = new Map()),
                (this._document = r);
            }
            register(t) {
              this.scrollContainers.has(t) ||
                this.scrollContainers.set(
                  t,
                  t.elementScrolled().subscribe(() => this._scrolled.next(t))
                );
            }
            deregister(t) {
              const i = this.scrollContainers.get(t);
              i && (i.unsubscribe(), this.scrollContainers.delete(t));
            }
            scrolled(t = 20) {
              return this._platform.isBrowser
                ? new fe((i) => {
                    this._globalSubscription || this._addGlobalListener();
                    const r =
                      t > 0
                        ? this._scrolled.pipe(AM(t)).subscribe(i)
                        : this._scrolled.subscribe(i);
                    return (
                      this._scrolledCount++,
                      () => {
                        r.unsubscribe(),
                          this._scrolledCount--,
                          this._scrolledCount || this._removeGlobalListener();
                      }
                    );
                  })
                : H();
            }
            ngOnDestroy() {
              this._removeGlobalListener(),
                this.scrollContainers.forEach((t, i) => this.deregister(i)),
                this._scrolled.complete();
            }
            ancestorScrolled(t, i) {
              const r = this.getAncestorScrollContainers(t);
              return this.scrolled(i).pipe(tn((s) => !s || r.indexOf(s) > -1));
            }
            getAncestorScrollContainers(t) {
              const i = [];
              return (
                this.scrollContainers.forEach((r, s) => {
                  this._scrollableContainsElement(s, t) && i.push(s);
                }),
                i
              );
            }
            _getWindow() {
              return this._document.defaultView || window;
            }
            _scrollableContainsElement(t, i) {
              let r = ei(i),
                s = t.getElementRef().nativeElement;
              do {
                if (r == s) return !0;
              } while ((r = r.parentElement));
              return !1;
            }
            _addGlobalListener() {
              this._globalSubscription = this._ngZone.runOutsideAngular(() =>
                Dc(this._getWindow().document, "scroll").subscribe(() =>
                  this._scrolled.next()
                )
              );
            }
            _removeGlobalListener() {
              this._globalSubscription &&
                (this._globalSubscription.unsubscribe(),
                (this._globalSubscription = null));
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(ee), b(Jt), b(ue, 8));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
            n
          );
        })(),
        Mp = (() => {
          class n {
            constructor(t, i, r) {
              (this._platform = t),
                (this._change = new le()),
                (this._changeListener = (s) => {
                  this._change.next(s);
                }),
                (this._document = r),
                i.runOutsideAngular(() => {
                  if (t.isBrowser) {
                    const s = this._getWindow();
                    s.addEventListener("resize", this._changeListener),
                      s.addEventListener(
                        "orientationchange",
                        this._changeListener
                      );
                  }
                  this.change().subscribe(() => (this._viewportSize = null));
                });
            }
            ngOnDestroy() {
              if (this._platform.isBrowser) {
                const t = this._getWindow();
                t.removeEventListener("resize", this._changeListener),
                  t.removeEventListener(
                    "orientationchange",
                    this._changeListener
                  );
              }
              this._change.complete();
            }
            getViewportSize() {
              this._viewportSize || this._updateViewportSize();
              const t = {
                width: this._viewportSize.width,
                height: this._viewportSize.height,
              };
              return this._platform.isBrowser || (this._viewportSize = null), t;
            }
            getViewportRect() {
              const t = this.getViewportScrollPosition(),
                { width: i, height: r } = this.getViewportSize();
              return {
                top: t.top,
                left: t.left,
                bottom: t.top + r,
                right: t.left + i,
                height: r,
                width: i,
              };
            }
            getViewportScrollPosition() {
              if (!this._platform.isBrowser) return { top: 0, left: 0 };
              const t = this._document,
                i = this._getWindow(),
                r = t.documentElement,
                s = r.getBoundingClientRect();
              return {
                top:
                  -s.top || t.body.scrollTop || i.scrollY || r.scrollTop || 0,
                left:
                  -s.left ||
                  t.body.scrollLeft ||
                  i.scrollX ||
                  r.scrollLeft ||
                  0,
              };
            }
            change(t = 20) {
              return t > 0 ? this._change.pipe(AM(t)) : this._change;
            }
            _getWindow() {
              return this._document.defaultView || window;
            }
            _updateViewportSize() {
              const t = this._getWindow();
              this._viewportSize = this._platform.isBrowser
                ? { width: t.innerWidth, height: t.innerHeight }
                : { width: 0, height: 0 };
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(Jt), b(ee), b(ue, 8));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
            n
          );
        })(),
        Sp = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({})),
            n
          );
        })(),
        TM = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({ imports: [[Io, Sp], Io, Sp] })),
            n
          );
        })();
      class Ap {
        attach(e) {
          return (this._attachedHost = e), e.attach(this);
        }
        detach() {
          let e = this._attachedHost;
          null != e && ((this._attachedHost = null), e.detach());
        }
        get isAttached() {
          return null != this._attachedHost;
        }
        setAttachedHost(e) {
          this._attachedHost = e;
        }
      }
      class T2 extends Ap {
        constructor(e, t, i, r) {
          super(),
            (this.component = e),
            (this.viewContainerRef = t),
            (this.injector = i),
            (this.componentFactoryResolver = r);
        }
      }
      class OM extends Ap {
        constructor(e, t, i) {
          super(),
            (this.templateRef = e),
            (this.viewContainerRef = t),
            (this.context = i);
        }
        get origin() {
          return this.templateRef.elementRef;
        }
        attach(e, t = this.context) {
          return (this.context = t), super.attach(e);
        }
        detach() {
          return (this.context = void 0), super.detach();
        }
      }
      class O2 extends Ap {
        constructor(e) {
          super(), (this.element = e instanceof Se ? e.nativeElement : e);
        }
      }
      class x2 extends class I2 {
        constructor() {
          (this._isDisposed = !1), (this.attachDomPortal = null);
        }
        hasAttached() {
          return !!this._attachedPortal;
        }
        attach(e) {
          return e instanceof T2
            ? ((this._attachedPortal = e), this.attachComponentPortal(e))
            : e instanceof OM
            ? ((this._attachedPortal = e), this.attachTemplatePortal(e))
            : this.attachDomPortal && e instanceof O2
            ? ((this._attachedPortal = e), this.attachDomPortal(e))
            : void 0;
        }
        detach() {
          this._attachedPortal &&
            (this._attachedPortal.setAttachedHost(null),
            (this._attachedPortal = null)),
            this._invokeDisposeFn();
        }
        dispose() {
          this.hasAttached() && this.detach(),
            this._invokeDisposeFn(),
            (this._isDisposed = !0);
        }
        setDisposeFn(e) {
          this._disposeFn = e;
        }
        _invokeDisposeFn() {
          this._disposeFn && (this._disposeFn(), (this._disposeFn = null));
        }
      } {
        constructor(e, t, i, r, s) {
          super(),
            (this.outletElement = e),
            (this._componentFactoryResolver = t),
            (this._appRef = i),
            (this._defaultInjector = r),
            (this.attachDomPortal = (o) => {
              const a = o.element,
                l = this._document.createComment("dom-portal");
              a.parentNode.insertBefore(l, a),
                this.outletElement.appendChild(a),
                (this._attachedPortal = o),
                super.setDisposeFn(() => {
                  l.parentNode && l.parentNode.replaceChild(a, l);
                });
            }),
            (this._document = s);
        }
        attachComponentPortal(e) {
          const i = (
            e.componentFactoryResolver || this._componentFactoryResolver
          ).resolveComponentFactory(e.component);
          let r;
          return (
            e.viewContainerRef
              ? ((r = e.viewContainerRef.createComponent(
                  i,
                  e.viewContainerRef.length,
                  e.injector || e.viewContainerRef.injector
                )),
                this.setDisposeFn(() => r.destroy()))
              : ((r = i.create(e.injector || this._defaultInjector || Qe.NULL)),
                this._appRef.attachView(r.hostView),
                this.setDisposeFn(() => {
                  this._appRef.viewCount > 0 &&
                    this._appRef.detachView(r.hostView),
                    r.destroy();
                })),
            this.outletElement.appendChild(this._getComponentRootNode(r)),
            (this._attachedPortal = e),
            r
          );
        }
        attachTemplatePortal(e) {
          let t = e.viewContainerRef,
            i = t.createEmbeddedView(e.templateRef, e.context);
          return (
            i.rootNodes.forEach((r) => this.outletElement.appendChild(r)),
            i.detectChanges(),
            this.setDisposeFn(() => {
              let r = t.indexOf(i);
              -1 !== r && t.remove(r);
            }),
            (this._attachedPortal = e),
            i
          );
        }
        dispose() {
          super.dispose(), this.outletElement.remove();
        }
        _getComponentRootNode(e) {
          return e.hostView.rootNodes[0];
        }
      }
      let k2 = (() => {
        class n {}
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵmod = he({ type: n })),
          (n.ɵinj = ce({})),
          n
        );
      })();
      const IM = _N();
      class R2 {
        constructor(e, t) {
          (this._viewportRuler = e),
            (this._previousHTMLStyles = { top: "", left: "" }),
            (this._isEnabled = !1),
            (this._document = t);
        }
        attach() {}
        enable() {
          if (this._canBeEnabled()) {
            const e = this._document.documentElement;
            (this._previousScrollPosition =
              this._viewportRuler.getViewportScrollPosition()),
              (this._previousHTMLStyles.left = e.style.left || ""),
              (this._previousHTMLStyles.top = e.style.top || ""),
              (e.style.left = qe(-this._previousScrollPosition.left)),
              (e.style.top = qe(-this._previousScrollPosition.top)),
              e.classList.add("cdk-global-scrollblock"),
              (this._isEnabled = !0);
          }
        }
        disable() {
          if (this._isEnabled) {
            const e = this._document.documentElement,
              i = e.style,
              r = this._document.body.style,
              s = i.scrollBehavior || "",
              o = r.scrollBehavior || "";
            (this._isEnabled = !1),
              (i.left = this._previousHTMLStyles.left),
              (i.top = this._previousHTMLStyles.top),
              e.classList.remove("cdk-global-scrollblock"),
              IM && (i.scrollBehavior = r.scrollBehavior = "auto"),
              window.scroll(
                this._previousScrollPosition.left,
                this._previousScrollPosition.top
              ),
              IM && ((i.scrollBehavior = s), (r.scrollBehavior = o));
          }
        }
        _canBeEnabled() {
          if (
            this._document.documentElement.classList.contains(
              "cdk-global-scrollblock"
            ) ||
            this._isEnabled
          )
            return !1;
          const t = this._document.body,
            i = this._viewportRuler.getViewportSize();
          return t.scrollHeight > i.height || t.scrollWidth > i.width;
        }
      }
      class P2 {
        constructor(e, t, i, r) {
          (this._scrollDispatcher = e),
            (this._ngZone = t),
            (this._viewportRuler = i),
            (this._config = r),
            (this._scrollSubscription = null),
            (this._detach = () => {
              this.disable(),
                this._overlayRef.hasAttached() &&
                  this._ngZone.run(() => this._overlayRef.detach());
            });
        }
        attach(e) {
          this._overlayRef = e;
        }
        enable() {
          if (this._scrollSubscription) return;
          const e = this._scrollDispatcher.scrolled(0);
          this._config && this._config.threshold && this._config.threshold > 1
            ? ((this._initialScrollPosition =
                this._viewportRuler.getViewportScrollPosition().top),
              (this._scrollSubscription = e.subscribe(() => {
                const t = this._viewportRuler.getViewportScrollPosition().top;
                Math.abs(t - this._initialScrollPosition) >
                this._config.threshold
                  ? this._detach()
                  : this._overlayRef.updatePosition();
              })))
            : (this._scrollSubscription = e.subscribe(this._detach));
        }
        disable() {
          this._scrollSubscription &&
            (this._scrollSubscription.unsubscribe(),
            (this._scrollSubscription = null));
        }
        detach() {
          this.disable(), (this._overlayRef = null);
        }
      }
      class xM {
        enable() {}
        disable() {}
        attach() {}
      }
      function Tp(n, e) {
        return e.some(
          (t) =>
            n.bottom < t.top ||
            n.top > t.bottom ||
            n.right < t.left ||
            n.left > t.right
        );
      }
      function kM(n, e) {
        return e.some(
          (t) =>
            n.top < t.top ||
            n.bottom > t.bottom ||
            n.left < t.left ||
            n.right > t.right
        );
      }
      class N2 {
        constructor(e, t, i, r) {
          (this._scrollDispatcher = e),
            (this._viewportRuler = t),
            (this._ngZone = i),
            (this._config = r),
            (this._scrollSubscription = null);
        }
        attach(e) {
          this._overlayRef = e;
        }
        enable() {
          this._scrollSubscription ||
            (this._scrollSubscription = this._scrollDispatcher
              .scrolled(this._config ? this._config.scrollThrottle : 0)
              .subscribe(() => {
                if (
                  (this._overlayRef.updatePosition(),
                  this._config && this._config.autoClose)
                ) {
                  const t =
                      this._overlayRef.overlayElement.getBoundingClientRect(),
                    { width: i, height: r } =
                      this._viewportRuler.getViewportSize();
                  Tp(t, [
                    {
                      width: i,
                      height: r,
                      bottom: r,
                      right: i,
                      top: 0,
                      left: 0,
                    },
                  ]) &&
                    (this.disable(),
                    this._ngZone.run(() => this._overlayRef.detach()));
                }
              }));
        }
        disable() {
          this._scrollSubscription &&
            (this._scrollSubscription.unsubscribe(),
            (this._scrollSubscription = null));
        }
        detach() {
          this.disable(), (this._overlayRef = null);
        }
      }
      let L2 = (() => {
        class n {
          constructor(t, i, r, s) {
            (this._scrollDispatcher = t),
              (this._viewportRuler = i),
              (this._ngZone = r),
              (this.noop = () => new xM()),
              (this.close = (o) =>
                new P2(
                  this._scrollDispatcher,
                  this._ngZone,
                  this._viewportRuler,
                  o
                )),
              (this.block = () => new R2(this._viewportRuler, this._document)),
              (this.reposition = (o) =>
                new N2(
                  this._scrollDispatcher,
                  this._viewportRuler,
                  this._ngZone,
                  o
                )),
              (this._document = s);
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(S2), b(Mp), b(ee), b(ue));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
          n
        );
      })();
      class FM {
        constructor(e) {
          if (
            ((this.scrollStrategy = new xM()),
            (this.panelClass = ""),
            (this.hasBackdrop = !1),
            (this.backdropClass = "cdk-overlay-dark-backdrop"),
            (this.disposeOnNavigation = !1),
            e)
          ) {
            const t = Object.keys(e);
            for (const i of t) void 0 !== e[i] && (this[i] = e[i]);
          }
        }
      }
      class V2 {
        constructor(e, t) {
          (this.connectionPair = e), (this.scrollableViewProperties = t);
        }
      }
      class B2 {
        constructor(e, t, i, r, s, o, a, l, c) {
          (this._portalOutlet = e),
            (this._host = t),
            (this._pane = i),
            (this._config = r),
            (this._ngZone = s),
            (this._keyboardDispatcher = o),
            (this._document = a),
            (this._location = l),
            (this._outsideClickDispatcher = c),
            (this._backdropElement = null),
            (this._backdropClick = new le()),
            (this._attachments = new le()),
            (this._detachments = new le()),
            (this._locationChanges = Le.EMPTY),
            (this._backdropClickHandler = (u) => this._backdropClick.next(u)),
            (this._backdropTransitionendHandler = (u) => {
              this._disposeBackdrop(u.target);
            }),
            (this._keydownEvents = new le()),
            (this._outsidePointerEvents = new le()),
            r.scrollStrategy &&
              ((this._scrollStrategy = r.scrollStrategy),
              this._scrollStrategy.attach(this)),
            (this._positionStrategy = r.positionStrategy);
        }
        get overlayElement() {
          return this._pane;
        }
        get backdropElement() {
          return this._backdropElement;
        }
        get hostElement() {
          return this._host;
        }
        attach(e) {
          !this._host.parentElement &&
            this._previousHostParent &&
            this._previousHostParent.appendChild(this._host);
          const t = this._portalOutlet.attach(e);
          return (
            this._positionStrategy && this._positionStrategy.attach(this),
            this._updateStackingOrder(),
            this._updateElementSize(),
            this._updateElementDirection(),
            this._scrollStrategy && this._scrollStrategy.enable(),
            this._ngZone.onStable.pipe(Un(1)).subscribe(() => {
              this.hasAttached() && this.updatePosition();
            }),
            this._togglePointerEvents(!0),
            this._config.hasBackdrop && this._attachBackdrop(),
            this._config.panelClass &&
              this._toggleClasses(this._pane, this._config.panelClass, !0),
            this._attachments.next(),
            this._keyboardDispatcher.add(this),
            this._config.disposeOnNavigation &&
              (this._locationChanges = this._location.subscribe(() =>
                this.dispose()
              )),
            this._outsideClickDispatcher.add(this),
            t
          );
        }
        detach() {
          if (!this.hasAttached()) return;
          this.detachBackdrop(),
            this._togglePointerEvents(!1),
            this._positionStrategy &&
              this._positionStrategy.detach &&
              this._positionStrategy.detach(),
            this._scrollStrategy && this._scrollStrategy.disable();
          const e = this._portalOutlet.detach();
          return (
            this._detachments.next(),
            this._keyboardDispatcher.remove(this),
            this._detachContentWhenStable(),
            this._locationChanges.unsubscribe(),
            this._outsideClickDispatcher.remove(this),
            e
          );
        }
        dispose() {
          var e;
          const t = this.hasAttached();
          this._positionStrategy && this._positionStrategy.dispose(),
            this._disposeScrollStrategy(),
            this._disposeBackdrop(this._backdropElement),
            this._locationChanges.unsubscribe(),
            this._keyboardDispatcher.remove(this),
            this._portalOutlet.dispose(),
            this._attachments.complete(),
            this._backdropClick.complete(),
            this._keydownEvents.complete(),
            this._outsidePointerEvents.complete(),
            this._outsideClickDispatcher.remove(this),
            null === (e = this._host) || void 0 === e || e.remove(),
            (this._previousHostParent = this._pane = this._host = null),
            t && this._detachments.next(),
            this._detachments.complete();
        }
        hasAttached() {
          return this._portalOutlet.hasAttached();
        }
        backdropClick() {
          return this._backdropClick;
        }
        attachments() {
          return this._attachments;
        }
        detachments() {
          return this._detachments;
        }
        keydownEvents() {
          return this._keydownEvents;
        }
        outsidePointerEvents() {
          return this._outsidePointerEvents;
        }
        getConfig() {
          return this._config;
        }
        updatePosition() {
          this._positionStrategy && this._positionStrategy.apply();
        }
        updatePositionStrategy(e) {
          e !== this._positionStrategy &&
            (this._positionStrategy && this._positionStrategy.dispose(),
            (this._positionStrategy = e),
            this.hasAttached() && (e.attach(this), this.updatePosition()));
        }
        updateSize(e) {
          (this._config = Object.assign(Object.assign({}, this._config), e)),
            this._updateElementSize();
        }
        setDirection(e) {
          (this._config = Object.assign(Object.assign({}, this._config), {
            direction: e,
          })),
            this._updateElementDirection();
        }
        addPanelClass(e) {
          this._pane && this._toggleClasses(this._pane, e, !0);
        }
        removePanelClass(e) {
          this._pane && this._toggleClasses(this._pane, e, !1);
        }
        getDirection() {
          const e = this._config.direction;
          return e ? ("string" == typeof e ? e : e.value) : "ltr";
        }
        updateScrollStrategy(e) {
          e !== this._scrollStrategy &&
            (this._disposeScrollStrategy(),
            (this._scrollStrategy = e),
            this.hasAttached() && (e.attach(this), e.enable()));
        }
        _updateElementDirection() {
          this._host.setAttribute("dir", this.getDirection());
        }
        _updateElementSize() {
          if (!this._pane) return;
          const e = this._pane.style;
          (e.width = qe(this._config.width)),
            (e.height = qe(this._config.height)),
            (e.minWidth = qe(this._config.minWidth)),
            (e.minHeight = qe(this._config.minHeight)),
            (e.maxWidth = qe(this._config.maxWidth)),
            (e.maxHeight = qe(this._config.maxHeight));
        }
        _togglePointerEvents(e) {
          this._pane.style.pointerEvents = e ? "" : "none";
        }
        _attachBackdrop() {
          const e = "cdk-overlay-backdrop-showing";
          (this._backdropElement = this._document.createElement("div")),
            this._backdropElement.classList.add("cdk-overlay-backdrop"),
            this._config.backdropClass &&
              this._toggleClasses(
                this._backdropElement,
                this._config.backdropClass,
                !0
              ),
            this._host.parentElement.insertBefore(
              this._backdropElement,
              this._host
            ),
            this._backdropElement.addEventListener(
              "click",
              this._backdropClickHandler
            ),
            "undefined" != typeof requestAnimationFrame
              ? this._ngZone.runOutsideAngular(() => {
                  requestAnimationFrame(() => {
                    this._backdropElement &&
                      this._backdropElement.classList.add(e);
                  });
                })
              : this._backdropElement.classList.add(e);
        }
        _updateStackingOrder() {
          this._host.nextSibling &&
            this._host.parentNode.appendChild(this._host);
        }
        detachBackdrop() {
          const e = this._backdropElement;
          !e ||
            (e.classList.remove("cdk-overlay-backdrop-showing"),
            this._ngZone.runOutsideAngular(() => {
              e.addEventListener(
                "transitionend",
                this._backdropTransitionendHandler
              );
            }),
            (e.style.pointerEvents = "none"),
            (this._backdropTimeout = this._ngZone.runOutsideAngular(() =>
              setTimeout(() => {
                this._disposeBackdrop(e);
              }, 500)
            )));
        }
        _toggleClasses(e, t, i) {
          const r = yC(t || []).filter((s) => !!s);
          r.length && (i ? e.classList.add(...r) : e.classList.remove(...r));
        }
        _detachContentWhenStable() {
          this._ngZone.runOutsideAngular(() => {
            const e = this._ngZone.onStable
              .pipe(Nt(lr(this._attachments, this._detachments)))
              .subscribe(() => {
                (!this._pane ||
                  !this._host ||
                  0 === this._pane.children.length) &&
                  (this._pane &&
                    this._config.panelClass &&
                    this._toggleClasses(
                      this._pane,
                      this._config.panelClass,
                      !1
                    ),
                  this._host &&
                    this._host.parentElement &&
                    ((this._previousHostParent = this._host.parentElement),
                    this._host.remove()),
                  e.unsubscribe());
              });
          });
        }
        _disposeScrollStrategy() {
          const e = this._scrollStrategy;
          e && (e.disable(), e.detach && e.detach());
        }
        _disposeBackdrop(e) {
          e &&
            (e.removeEventListener("click", this._backdropClickHandler),
            e.removeEventListener(
              "transitionend",
              this._backdropTransitionendHandler
            ),
            e.remove(),
            this._backdropElement === e && (this._backdropElement = null)),
            this._backdropTimeout &&
              (clearTimeout(this._backdropTimeout),
              (this._backdropTimeout = void 0));
        }
      }
      let RM = (() => {
        class n {
          constructor(t, i) {
            (this._platform = i), (this._document = t);
          }
          ngOnDestroy() {
            var t;
            null === (t = this._containerElement) || void 0 === t || t.remove();
          }
          getContainerElement() {
            return (
              this._containerElement || this._createContainer(),
              this._containerElement
            );
          }
          _createContainer() {
            const t = "cdk-overlay-container";
            if (this._platform.isBrowser || nf()) {
              const r = this._document.querySelectorAll(
                `.${t}[platform="server"], .${t}[platform="test"]`
              );
              for (let s = 0; s < r.length; s++) r[s].remove();
            }
            const i = this._document.createElement("div");
            i.classList.add(t),
              nf()
                ? i.setAttribute("platform", "test")
                : this._platform.isBrowser ||
                  i.setAttribute("platform", "server"),
              this._document.body.appendChild(i),
              (this._containerElement = i);
          }
        }
        return (
          (n.ɵfac = function (t) {
            return new (t || n)(b(ue), b(Jt));
          }),
          (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
          n
        );
      })();
      const PM = "cdk-overlay-connected-position-bounding-box",
        j2 = /([A-Za-z%]+)$/;
      class H2 {
        constructor(e, t, i, r, s) {
          (this._viewportRuler = t),
            (this._document = i),
            (this._platform = r),
            (this._overlayContainer = s),
            (this._lastBoundingBoxSize = { width: 0, height: 0 }),
            (this._isPushed = !1),
            (this._canPush = !0),
            (this._growAfterOpen = !1),
            (this._hasFlexibleDimensions = !0),
            (this._positionLocked = !1),
            (this._viewportMargin = 0),
            (this._scrollables = []),
            (this._preferredPositions = []),
            (this._positionChanges = new le()),
            (this._resizeSubscription = Le.EMPTY),
            (this._offsetX = 0),
            (this._offsetY = 0),
            (this._appliedPanelClasses = []),
            (this.positionChanges = this._positionChanges),
            this.setOrigin(e);
        }
        get positions() {
          return this._preferredPositions;
        }
        attach(e) {
          this._validatePositions(),
            e.hostElement.classList.add(PM),
            (this._overlayRef = e),
            (this._boundingBox = e.hostElement),
            (this._pane = e.overlayElement),
            (this._isDisposed = !1),
            (this._isInitialRender = !0),
            (this._lastPosition = null),
            this._resizeSubscription.unsubscribe(),
            (this._resizeSubscription = this._viewportRuler
              .change()
              .subscribe(() => {
                (this._isInitialRender = !0), this.apply();
              }));
        }
        apply() {
          if (this._isDisposed || !this._platform.isBrowser) return;
          if (
            !this._isInitialRender &&
            this._positionLocked &&
            this._lastPosition
          )
            return void this.reapplyLastPosition();
          this._clearPanelClasses(),
            this._resetOverlayElementStyles(),
            this._resetBoundingBoxStyles(),
            (this._viewportRect = this._getNarrowedViewportRect()),
            (this._originRect = this._getOriginRect()),
            (this._overlayRect = this._pane.getBoundingClientRect()),
            (this._containerRect = this._overlayContainer
              .getContainerElement()
              .getBoundingClientRect());
          const e = this._originRect,
            t = this._overlayRect,
            i = this._viewportRect,
            r = this._containerRect,
            s = [];
          let o;
          for (let a of this._preferredPositions) {
            let l = this._getOriginPoint(e, r, a),
              c = this._getOverlayPoint(l, t, a),
              u = this._getOverlayFit(c, t, i, a);
            if (u.isCompletelyWithinViewport)
              return (this._isPushed = !1), void this._applyPosition(a, l);
            this._canFitWithFlexibleDimensions(u, c, i)
              ? s.push({
                  position: a,
                  origin: l,
                  overlayRect: t,
                  boundingBoxRect: this._calculateBoundingBoxRect(l, a),
                })
              : (!o || o.overlayFit.visibleArea < u.visibleArea) &&
                (o = {
                  overlayFit: u,
                  overlayPoint: c,
                  originPoint: l,
                  position: a,
                  overlayRect: t,
                });
          }
          if (s.length) {
            let a = null,
              l = -1;
            for (const c of s) {
              const u =
                c.boundingBoxRect.width *
                c.boundingBoxRect.height *
                (c.position.weight || 1);
              u > l && ((l = u), (a = c));
            }
            return (
              (this._isPushed = !1),
              void this._applyPosition(a.position, a.origin)
            );
          }
          if (this._canPush)
            return (
              (this._isPushed = !0),
              void this._applyPosition(o.position, o.originPoint)
            );
          this._applyPosition(o.position, o.originPoint);
        }
        detach() {
          this._clearPanelClasses(),
            (this._lastPosition = null),
            (this._previousPushAmount = null),
            this._resizeSubscription.unsubscribe();
        }
        dispose() {
          this._isDisposed ||
            (this._boundingBox &&
              rr(this._boundingBox.style, {
                top: "",
                left: "",
                right: "",
                bottom: "",
                height: "",
                width: "",
                alignItems: "",
                justifyContent: "",
              }),
            this._pane && this._resetOverlayElementStyles(),
            this._overlayRef &&
              this._overlayRef.hostElement.classList.remove(PM),
            this.detach(),
            this._positionChanges.complete(),
            (this._overlayRef = this._boundingBox = null),
            (this._isDisposed = !0));
        }
        reapplyLastPosition() {
          if (this._isDisposed || !this._platform.isBrowser) return;
          const e = this._lastPosition;
          if (e) {
            (this._originRect = this._getOriginRect()),
              (this._overlayRect = this._pane.getBoundingClientRect()),
              (this._viewportRect = this._getNarrowedViewportRect()),
              (this._containerRect = this._overlayContainer
                .getContainerElement()
                .getBoundingClientRect());
            const t = this._getOriginPoint(
              this._originRect,
              this._containerRect,
              e
            );
            this._applyPosition(e, t);
          } else this.apply();
        }
        withScrollableContainers(e) {
          return (this._scrollables = e), this;
        }
        withPositions(e) {
          return (
            (this._preferredPositions = e),
            -1 === e.indexOf(this._lastPosition) && (this._lastPosition = null),
            this._validatePositions(),
            this
          );
        }
        withViewportMargin(e) {
          return (this._viewportMargin = e), this;
        }
        withFlexibleDimensions(e = !0) {
          return (this._hasFlexibleDimensions = e), this;
        }
        withGrowAfterOpen(e = !0) {
          return (this._growAfterOpen = e), this;
        }
        withPush(e = !0) {
          return (this._canPush = e), this;
        }
        withLockedPosition(e = !0) {
          return (this._positionLocked = e), this;
        }
        setOrigin(e) {
          return (this._origin = e), this;
        }
        withDefaultOffsetX(e) {
          return (this._offsetX = e), this;
        }
        withDefaultOffsetY(e) {
          return (this._offsetY = e), this;
        }
        withTransformOriginOn(e) {
          return (this._transformOriginSelector = e), this;
        }
        _getOriginPoint(e, t, i) {
          let r, s;
          if ("center" == i.originX) r = e.left + e.width / 2;
          else {
            const o = this._isRtl() ? e.right : e.left,
              a = this._isRtl() ? e.left : e.right;
            r = "start" == i.originX ? o : a;
          }
          return (
            t.left < 0 && (r -= t.left),
            (s =
              "center" == i.originY
                ? e.top + e.height / 2
                : "top" == i.originY
                ? e.top
                : e.bottom),
            t.top < 0 && (s -= t.top),
            { x: r, y: s }
          );
        }
        _getOverlayPoint(e, t, i) {
          let r, s;
          return (
            (r =
              "center" == i.overlayX
                ? -t.width / 2
                : "start" === i.overlayX
                ? this._isRtl()
                  ? -t.width
                  : 0
                : this._isRtl()
                ? 0
                : -t.width),
            (s =
              "center" == i.overlayY
                ? -t.height / 2
                : "top" == i.overlayY
                ? 0
                : -t.height),
            { x: e.x + r, y: e.y + s }
          );
        }
        _getOverlayFit(e, t, i, r) {
          const s = LM(t);
          let { x: o, y: a } = e,
            l = this._getOffset(r, "x"),
            c = this._getOffset(r, "y");
          l && (o += l), c && (a += c);
          let h = 0 - a,
            f = a + s.height - i.height,
            p = this._subtractOverflows(s.width, 0 - o, o + s.width - i.width),
            g = this._subtractOverflows(s.height, h, f),
            y = p * g;
          return {
            visibleArea: y,
            isCompletelyWithinViewport: s.width * s.height === y,
            fitsInViewportVertically: g === s.height,
            fitsInViewportHorizontally: p == s.width,
          };
        }
        _canFitWithFlexibleDimensions(e, t, i) {
          if (this._hasFlexibleDimensions) {
            const r = i.bottom - t.y,
              s = i.right - t.x,
              o = NM(this._overlayRef.getConfig().minHeight),
              a = NM(this._overlayRef.getConfig().minWidth),
              c = e.fitsInViewportHorizontally || (null != a && a <= s);
            return (e.fitsInViewportVertically || (null != o && o <= r)) && c;
          }
          return !1;
        }
        _pushOverlayOnScreen(e, t, i) {
          if (this._previousPushAmount && this._positionLocked)
            return {
              x: e.x + this._previousPushAmount.x,
              y: e.y + this._previousPushAmount.y,
            };
          const r = LM(t),
            s = this._viewportRect,
            o = Math.max(e.x + r.width - s.width, 0),
            a = Math.max(e.y + r.height - s.height, 0),
            l = Math.max(s.top - i.top - e.y, 0),
            c = Math.max(s.left - i.left - e.x, 0);
          let u = 0,
            d = 0;
          return (
            (u =
              r.width <= s.width
                ? c || -o
                : e.x < this._viewportMargin
                ? s.left - i.left - e.x
                : 0),
            (d =
              r.height <= s.height
                ? l || -a
                : e.y < this._viewportMargin
                ? s.top - i.top - e.y
                : 0),
            (this._previousPushAmount = { x: u, y: d }),
            { x: e.x + u, y: e.y + d }
          );
        }
        _applyPosition(e, t) {
          if (
            (this._setTransformOrigin(e),
            this._setOverlayElementStyles(t, e),
            this._setBoundingBoxStyles(t, e),
            e.panelClass && this._addPanelClasses(e.panelClass),
            (this._lastPosition = e),
            this._positionChanges.observers.length)
          ) {
            const i = this._getScrollVisibility(),
              r = new V2(e, i);
            this._positionChanges.next(r);
          }
          this._isInitialRender = !1;
        }
        _setTransformOrigin(e) {
          if (!this._transformOriginSelector) return;
          const t = this._boundingBox.querySelectorAll(
            this._transformOriginSelector
          );
          let i,
            r = e.overlayY;
          i =
            "center" === e.overlayX
              ? "center"
              : this._isRtl()
              ? "start" === e.overlayX
                ? "right"
                : "left"
              : "start" === e.overlayX
              ? "left"
              : "right";
          for (let s = 0; s < t.length; s++)
            t[s].style.transformOrigin = `${i} ${r}`;
        }
        _calculateBoundingBoxRect(e, t) {
          const i = this._viewportRect,
            r = this._isRtl();
          let s, o, a, u, d, h;
          if ("top" === t.overlayY)
            (o = e.y), (s = i.height - o + this._viewportMargin);
          else if ("bottom" === t.overlayY)
            (a = i.height - e.y + 2 * this._viewportMargin),
              (s = i.height - a + this._viewportMargin);
          else {
            const f = Math.min(i.bottom - e.y + i.top, e.y),
              p = this._lastBoundingBoxSize.height;
            (s = 2 * f),
              (o = e.y - f),
              s > p &&
                !this._isInitialRender &&
                !this._growAfterOpen &&
                (o = e.y - p / 2);
          }
          if (("end" === t.overlayX && !r) || ("start" === t.overlayX && r))
            (h = i.width - e.x + this._viewportMargin),
              (u = e.x - this._viewportMargin);
          else if (
            ("start" === t.overlayX && !r) ||
            ("end" === t.overlayX && r)
          )
            (d = e.x), (u = i.right - e.x);
          else {
            const f = Math.min(i.right - e.x + i.left, e.x),
              p = this._lastBoundingBoxSize.width;
            (u = 2 * f),
              (d = e.x - f),
              u > p &&
                !this._isInitialRender &&
                !this._growAfterOpen &&
                (d = e.x - p / 2);
          }
          return { top: o, left: d, bottom: a, right: h, width: u, height: s };
        }
        _setBoundingBoxStyles(e, t) {
          const i = this._calculateBoundingBoxRect(e, t);
          !this._isInitialRender &&
            !this._growAfterOpen &&
            ((i.height = Math.min(i.height, this._lastBoundingBoxSize.height)),
            (i.width = Math.min(i.width, this._lastBoundingBoxSize.width)));
          const r = {};
          if (this._hasExactPosition())
            (r.top = r.left = "0"),
              (r.bottom = r.right = r.maxHeight = r.maxWidth = ""),
              (r.width = r.height = "100%");
          else {
            const s = this._overlayRef.getConfig().maxHeight,
              o = this._overlayRef.getConfig().maxWidth;
            (r.height = qe(i.height)),
              (r.top = qe(i.top)),
              (r.bottom = qe(i.bottom)),
              (r.width = qe(i.width)),
              (r.left = qe(i.left)),
              (r.right = qe(i.right)),
              (r.alignItems =
                "center" === t.overlayX
                  ? "center"
                  : "end" === t.overlayX
                  ? "flex-end"
                  : "flex-start"),
              (r.justifyContent =
                "center" === t.overlayY
                  ? "center"
                  : "bottom" === t.overlayY
                  ? "flex-end"
                  : "flex-start"),
              s && (r.maxHeight = qe(s)),
              o && (r.maxWidth = qe(o));
          }
          (this._lastBoundingBoxSize = i), rr(this._boundingBox.style, r);
        }
        _resetBoundingBoxStyles() {
          rr(this._boundingBox.style, {
            top: "0",
            left: "0",
            right: "0",
            bottom: "0",
            height: "",
            width: "",
            alignItems: "",
            justifyContent: "",
          });
        }
        _resetOverlayElementStyles() {
          rr(this._pane.style, {
            top: "",
            left: "",
            bottom: "",
            right: "",
            position: "",
            transform: "",
          });
        }
        _setOverlayElementStyles(e, t) {
          const i = {},
            r = this._hasExactPosition(),
            s = this._hasFlexibleDimensions,
            o = this._overlayRef.getConfig();
          if (r) {
            const u = this._viewportRuler.getViewportScrollPosition();
            rr(i, this._getExactOverlayY(t, e, u)),
              rr(i, this._getExactOverlayX(t, e, u));
          } else i.position = "static";
          let a = "",
            l = this._getOffset(t, "x"),
            c = this._getOffset(t, "y");
          l && (a += `translateX(${l}px) `),
            c && (a += `translateY(${c}px)`),
            (i.transform = a.trim()),
            o.maxHeight &&
              (r ? (i.maxHeight = qe(o.maxHeight)) : s && (i.maxHeight = "")),
            o.maxWidth &&
              (r ? (i.maxWidth = qe(o.maxWidth)) : s && (i.maxWidth = "")),
            rr(this._pane.style, i);
        }
        _getExactOverlayY(e, t, i) {
          let r = { top: "", bottom: "" },
            s = this._getOverlayPoint(t, this._overlayRect, e);
          return (
            this._isPushed &&
              (s = this._pushOverlayOnScreen(s, this._overlayRect, i)),
            "bottom" === e.overlayY
              ? (r.bottom =
                  this._document.documentElement.clientHeight -
                  (s.y + this._overlayRect.height) +
                  "px")
              : (r.top = qe(s.y)),
            r
          );
        }
        _getExactOverlayX(e, t, i) {
          let o,
            r = { left: "", right: "" },
            s = this._getOverlayPoint(t, this._overlayRect, e);
          return (
            this._isPushed &&
              (s = this._pushOverlayOnScreen(s, this._overlayRect, i)),
            (o = this._isRtl()
              ? "end" === e.overlayX
                ? "left"
                : "right"
              : "end" === e.overlayX
              ? "right"
              : "left"),
            "right" === o
              ? (r.right =
                  this._document.documentElement.clientWidth -
                  (s.x + this._overlayRect.width) +
                  "px")
              : (r.left = qe(s.x)),
            r
          );
        }
        _getScrollVisibility() {
          const e = this._getOriginRect(),
            t = this._pane.getBoundingClientRect(),
            i = this._scrollables.map((r) =>
              r.getElementRef().nativeElement.getBoundingClientRect()
            );
          return {
            isOriginClipped: kM(e, i),
            isOriginOutsideView: Tp(e, i),
            isOverlayClipped: kM(t, i),
            isOverlayOutsideView: Tp(t, i),
          };
        }
        _subtractOverflows(e, ...t) {
          return t.reduce((i, r) => i - Math.max(r, 0), e);
        }
        _getNarrowedViewportRect() {
          const e = this._document.documentElement.clientWidth,
            t = this._document.documentElement.clientHeight,
            i = this._viewportRuler.getViewportScrollPosition();
          return {
            top: i.top + this._viewportMargin,
            left: i.left + this._viewportMargin,
            right: i.left + e - this._viewportMargin,
            bottom: i.top + t - this._viewportMargin,
            width: e - 2 * this._viewportMargin,
            height: t - 2 * this._viewportMargin,
          };
        }
        _isRtl() {
          return "rtl" === this._overlayRef.getDirection();
        }
        _hasExactPosition() {
          return !this._hasFlexibleDimensions || this._isPushed;
        }
        _getOffset(e, t) {
          return "x" === t
            ? null == e.offsetX
              ? this._offsetX
              : e.offsetX
            : null == e.offsetY
            ? this._offsetY
            : e.offsetY;
        }
        _validatePositions() {}
        _addPanelClasses(e) {
          this._pane &&
            yC(e).forEach((t) => {
              "" !== t &&
                -1 === this._appliedPanelClasses.indexOf(t) &&
                (this._appliedPanelClasses.push(t),
                this._pane.classList.add(t));
            });
        }
        _clearPanelClasses() {
          this._pane &&
            (this._appliedPanelClasses.forEach((e) => {
              this._pane.classList.remove(e);
            }),
            (this._appliedPanelClasses = []));
        }
        _getOriginRect() {
          const e = this._origin;
          if (e instanceof Se) return e.nativeElement.getBoundingClientRect();
          if (e instanceof Element) return e.getBoundingClientRect();
          const t = e.width || 0,
            i = e.height || 0;
          return {
            top: e.y,
            bottom: e.y + i,
            left: e.x,
            right: e.x + t,
            height: i,
            width: t,
          };
        }
      }
      function rr(n, e) {
        for (let t in e) e.hasOwnProperty(t) && (n[t] = e[t]);
        return n;
      }
      function NM(n) {
        if ("number" != typeof n && null != n) {
          const [e, t] = n.split(j2);
          return t && "px" !== t ? null : parseFloat(e);
        }
        return n || null;
      }
      function LM(n) {
        return {
          top: Math.floor(n.top),
          right: Math.floor(n.right),
          bottom: Math.floor(n.bottom),
          left: Math.floor(n.left),
          width: Math.floor(n.width),
          height: Math.floor(n.height),
        };
      }
      const VM = "cdk-global-overlay-wrapper";
      class U2 {
        constructor() {
          (this._cssPosition = "static"),
            (this._topOffset = ""),
            (this._bottomOffset = ""),
            (this._leftOffset = ""),
            (this._rightOffset = ""),
            (this._alignItems = ""),
            (this._justifyContent = ""),
            (this._width = ""),
            (this._height = "");
        }
        attach(e) {
          const t = e.getConfig();
          (this._overlayRef = e),
            this._width && !t.width && e.updateSize({ width: this._width }),
            this._height && !t.height && e.updateSize({ height: this._height }),
            e.hostElement.classList.add(VM),
            (this._isDisposed = !1);
        }
        top(e = "") {
          return (
            (this._bottomOffset = ""),
            (this._topOffset = e),
            (this._alignItems = "flex-start"),
            this
          );
        }
        left(e = "") {
          return (
            (this._rightOffset = ""),
            (this._leftOffset = e),
            (this._justifyContent = "flex-start"),
            this
          );
        }
        bottom(e = "") {
          return (
            (this._topOffset = ""),
            (this._bottomOffset = e),
            (this._alignItems = "flex-end"),
            this
          );
        }
        right(e = "") {
          return (
            (this._leftOffset = ""),
            (this._rightOffset = e),
            (this._justifyContent = "flex-end"),
            this
          );
        }
        width(e = "") {
          return (
            this._overlayRef
              ? this._overlayRef.updateSize({ width: e })
              : (this._width = e),
            this
          );
        }
        height(e = "") {
          return (
            this._overlayRef
              ? this._overlayRef.updateSize({ height: e })
              : (this._height = e),
            this
          );
        }
        centerHorizontally(e = "") {
          return this.left(e), (this._justifyContent = "center"), this;
        }
        centerVertically(e = "") {
          return this.top(e), (this._alignItems = "center"), this;
        }
        apply() {
          if (!this._overlayRef || !this._overlayRef.hasAttached()) return;
          const e = this._overlayRef.overlayElement.style,
            t = this._overlayRef.hostElement.style,
            i = this._overlayRef.getConfig(),
            { width: r, height: s, maxWidth: o, maxHeight: a } = i,
            l = !(
              ("100%" !== r && "100vw" !== r) ||
              (o && "100%" !== o && "100vw" !== o)
            ),
            c = !(
              ("100%" !== s && "100vh" !== s) ||
              (a && "100%" !== a && "100vh" !== a)
            );
          (e.position = this._cssPosition),
            (e.marginLeft = l ? "0" : this._leftOffset),
            (e.marginTop = c ? "0" : this._topOffset),
            (e.marginBottom = this._bottomOffset),
            (e.marginRight = this._rightOffset),
            l
              ? (t.justifyContent = "flex-start")
              : "center" === this._justifyContent
              ? (t.justifyContent = "center")
              : "rtl" === this._overlayRef.getConfig().direction
              ? "flex-start" === this._justifyContent
                ? (t.justifyContent = "flex-end")
                : "flex-end" === this._justifyContent &&
                  (t.justifyContent = "flex-start")
              : (t.justifyContent = this._justifyContent),
            (t.alignItems = c ? "flex-start" : this._alignItems);
        }
        dispose() {
          if (this._isDisposed || !this._overlayRef) return;
          const e = this._overlayRef.overlayElement.style,
            t = this._overlayRef.hostElement,
            i = t.style;
          t.classList.remove(VM),
            (i.justifyContent =
              i.alignItems =
              e.marginTop =
              e.marginBottom =
              e.marginLeft =
              e.marginRight =
              e.position =
                ""),
            (this._overlayRef = null),
            (this._isDisposed = !0);
        }
      }
      let $2 = (() => {
          class n {
            constructor(t, i, r, s) {
              (this._viewportRuler = t),
                (this._document = i),
                (this._platform = r),
                (this._overlayContainer = s);
            }
            global() {
              return new U2();
            }
            flexibleConnectedTo(t) {
              return new H2(
                t,
                this._viewportRuler,
                this._document,
                this._platform,
                this._overlayContainer
              );
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(Mp), b(ue), b(Jt), b(RM));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
            n
          );
        })(),
        BM = (() => {
          class n {
            constructor(t) {
              (this._attachedOverlays = []), (this._document = t);
            }
            ngOnDestroy() {
              this.detach();
            }
            add(t) {
              this.remove(t), this._attachedOverlays.push(t);
            }
            remove(t) {
              const i = this._attachedOverlays.indexOf(t);
              i > -1 && this._attachedOverlays.splice(i, 1),
                0 === this._attachedOverlays.length && this.detach();
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(ue));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
            n
          );
        })(),
        z2 = (() => {
          class n extends BM {
            constructor(t, i) {
              super(t),
                (this._ngZone = i),
                (this._keydownListener = (r) => {
                  const s = this._attachedOverlays;
                  for (let o = s.length - 1; o > -1; o--)
                    if (s[o]._keydownEvents.observers.length > 0) {
                      const a = s[o]._keydownEvents;
                      this._ngZone
                        ? this._ngZone.run(() => a.next(r))
                        : a.next(r);
                      break;
                    }
                });
            }
            add(t) {
              super.add(t),
                this._isAttached ||
                  (this._ngZone
                    ? this._ngZone.runOutsideAngular(() =>
                        this._document.body.addEventListener(
                          "keydown",
                          this._keydownListener
                        )
                      )
                    : this._document.body.addEventListener(
                        "keydown",
                        this._keydownListener
                      ),
                  (this._isAttached = !0));
            }
            detach() {
              this._isAttached &&
                (this._document.body.removeEventListener(
                  "keydown",
                  this._keydownListener
                ),
                (this._isAttached = !1));
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(ue), b(ee, 8));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
            n
          );
        })(),
        G2 = (() => {
          class n extends BM {
            constructor(t, i, r) {
              super(t),
                (this._platform = i),
                (this._ngZone = r),
                (this._cursorStyleIsSet = !1),
                (this._pointerDownListener = (s) => {
                  this._pointerDownEventTarget = Yi(s);
                }),
                (this._clickListener = (s) => {
                  const o = Yi(s),
                    a =
                      "click" === s.type && this._pointerDownEventTarget
                        ? this._pointerDownEventTarget
                        : o;
                  this._pointerDownEventTarget = null;
                  const l = this._attachedOverlays.slice();
                  for (let c = l.length - 1; c > -1; c--) {
                    const u = l[c];
                    if (
                      u._outsidePointerEvents.observers.length < 1 ||
                      !u.hasAttached()
                    )
                      continue;
                    if (
                      u.overlayElement.contains(o) ||
                      u.overlayElement.contains(a)
                    )
                      break;
                    const d = u._outsidePointerEvents;
                    this._ngZone
                      ? this._ngZone.run(() => d.next(s))
                      : d.next(s);
                  }
                });
            }
            add(t) {
              if ((super.add(t), !this._isAttached)) {
                const i = this._document.body;
                this._ngZone
                  ? this._ngZone.runOutsideAngular(() =>
                      this._addEventListeners(i)
                    )
                  : this._addEventListeners(i),
                  this._platform.IOS &&
                    !this._cursorStyleIsSet &&
                    ((this._cursorOriginalValue = i.style.cursor),
                    (i.style.cursor = "pointer"),
                    (this._cursorStyleIsSet = !0)),
                  (this._isAttached = !0);
              }
            }
            detach() {
              if (this._isAttached) {
                const t = this._document.body;
                t.removeEventListener(
                  "pointerdown",
                  this._pointerDownListener,
                  !0
                ),
                  t.removeEventListener("click", this._clickListener, !0),
                  t.removeEventListener("auxclick", this._clickListener, !0),
                  t.removeEventListener("contextmenu", this._clickListener, !0),
                  this._platform.IOS &&
                    this._cursorStyleIsSet &&
                    ((t.style.cursor = this._cursorOriginalValue),
                    (this._cursorStyleIsSet = !1)),
                  (this._isAttached = !1);
              }
            }
            _addEventListeners(t) {
              t.addEventListener("pointerdown", this._pointerDownListener, !0),
                t.addEventListener("click", this._clickListener, !0),
                t.addEventListener("auxclick", this._clickListener, !0),
                t.addEventListener("contextmenu", this._clickListener, !0);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(ue), b(Jt), b(ee, 8));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
            n
          );
        })(),
        q2 = 0,
        Tc = (() => {
          class n {
            constructor(t, i, r, s, o, a, l, c, u, d, h) {
              (this.scrollStrategies = t),
                (this._overlayContainer = i),
                (this._componentFactoryResolver = r),
                (this._positionBuilder = s),
                (this._keyboardDispatcher = o),
                (this._injector = a),
                (this._ngZone = l),
                (this._document = c),
                (this._directionality = u),
                (this._location = d),
                (this._outsideClickDispatcher = h);
            }
            create(t) {
              const i = this._createHostElement(),
                r = this._createPaneElement(i),
                s = this._createPortalOutlet(r),
                o = new FM(t);
              return (
                (o.direction = o.direction || this._directionality.value),
                new B2(
                  s,
                  i,
                  r,
                  o,
                  this._ngZone,
                  this._keyboardDispatcher,
                  this._document,
                  this._location,
                  this._outsideClickDispatcher
                )
              );
            }
            position() {
              return this._positionBuilder;
            }
            _createPaneElement(t) {
              const i = this._document.createElement("div");
              return (
                (i.id = "cdk-overlay-" + q2++),
                i.classList.add("cdk-overlay-pane"),
                t.appendChild(i),
                i
              );
            }
            _createHostElement() {
              const t = this._document.createElement("div");
              return (
                this._overlayContainer.getContainerElement().appendChild(t), t
              );
            }
            _createPortalOutlet(t) {
              return (
                this._appRef || (this._appRef = this._injector.get(es)),
                new x2(
                  t,
                  this._componentFactoryResolver,
                  this._appRef,
                  this._injector,
                  this._document
                )
              );
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(
                b(L2),
                b(RM),
                b($i),
                b($2),
                b(z2),
                b(Qe),
                b(ee),
                b(ue),
                b(Nl),
                b(ll),
                b(G2)
              );
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac })),
            n
          );
        })();
      const W2 = [
          {
            originX: "start",
            originY: "bottom",
            overlayX: "start",
            overlayY: "top",
          },
          {
            originX: "start",
            originY: "top",
            overlayX: "start",
            overlayY: "bottom",
          },
          {
            originX: "end",
            originY: "top",
            overlayX: "end",
            overlayY: "bottom",
          },
          {
            originX: "end",
            originY: "bottom",
            overlayX: "end",
            overlayY: "top",
          },
        ],
        jM = new T("cdk-connected-overlay-scroll-strategy");
      let HM = (() => {
          class n {
            constructor(t) {
              this.elementRef = t;
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(Se));
            }),
            (n.ɵdir = x({
              type: n,
              selectors: [
                ["", "cdk-overlay-origin", ""],
                ["", "overlay-origin", ""],
                ["", "cdkOverlayOrigin", ""],
              ],
              exportAs: ["cdkOverlayOrigin"],
            })),
            n
          );
        })(),
        UM = (() => {
          class n {
            constructor(t, i, r, s, o) {
              (this._overlay = t),
                (this._dir = o),
                (this._hasBackdrop = !1),
                (this._lockPosition = !1),
                (this._growAfterOpen = !1),
                (this._flexibleDimensions = !1),
                (this._push = !1),
                (this._backdropSubscription = Le.EMPTY),
                (this._attachSubscription = Le.EMPTY),
                (this._detachSubscription = Le.EMPTY),
                (this._positionSubscription = Le.EMPTY),
                (this.viewportMargin = 0),
                (this.open = !1),
                (this.disableClose = !1),
                (this.backdropClick = new Q()),
                (this.positionChange = new Q()),
                (this.attach = new Q()),
                (this.detach = new Q()),
                (this.overlayKeydown = new Q()),
                (this.overlayOutsideClick = new Q()),
                (this._templatePortal = new OM(i, r)),
                (this._scrollStrategyFactory = s),
                (this.scrollStrategy = this._scrollStrategyFactory());
            }
            get offsetX() {
              return this._offsetX;
            }
            set offsetX(t) {
              (this._offsetX = t),
                this._position && this._updatePositionStrategy(this._position);
            }
            get offsetY() {
              return this._offsetY;
            }
            set offsetY(t) {
              (this._offsetY = t),
                this._position && this._updatePositionStrategy(this._position);
            }
            get hasBackdrop() {
              return this._hasBackdrop;
            }
            set hasBackdrop(t) {
              this._hasBackdrop = je(t);
            }
            get lockPosition() {
              return this._lockPosition;
            }
            set lockPosition(t) {
              this._lockPosition = je(t);
            }
            get flexibleDimensions() {
              return this._flexibleDimensions;
            }
            set flexibleDimensions(t) {
              this._flexibleDimensions = je(t);
            }
            get growAfterOpen() {
              return this._growAfterOpen;
            }
            set growAfterOpen(t) {
              this._growAfterOpen = je(t);
            }
            get push() {
              return this._push;
            }
            set push(t) {
              this._push = je(t);
            }
            get overlayRef() {
              return this._overlayRef;
            }
            get dir() {
              return this._dir ? this._dir.value : "ltr";
            }
            ngOnDestroy() {
              this._attachSubscription.unsubscribe(),
                this._detachSubscription.unsubscribe(),
                this._backdropSubscription.unsubscribe(),
                this._positionSubscription.unsubscribe(),
                this._overlayRef && this._overlayRef.dispose();
            }
            ngOnChanges(t) {
              this._position &&
                (this._updatePositionStrategy(this._position),
                this._overlayRef.updateSize({
                  width: this.width,
                  minWidth: this.minWidth,
                  height: this.height,
                  minHeight: this.minHeight,
                }),
                t.origin && this.open && this._position.apply()),
                t.open &&
                  (this.open ? this._attachOverlay() : this._detachOverlay());
            }
            _createOverlay() {
              (!this.positions || !this.positions.length) &&
                (this.positions = W2);
              const t = (this._overlayRef = this._overlay.create(
                this._buildConfig()
              ));
              (this._attachSubscription = t
                .attachments()
                .subscribe(() => this.attach.emit())),
                (this._detachSubscription = t
                  .detachments()
                  .subscribe(() => this.detach.emit())),
                t.keydownEvents().subscribe((i) => {
                  this.overlayKeydown.next(i),
                    27 === i.keyCode &&
                      !this.disableClose &&
                      !ko(i) &&
                      (i.preventDefault(), this._detachOverlay());
                }),
                this._overlayRef.outsidePointerEvents().subscribe((i) => {
                  this.overlayOutsideClick.next(i);
                });
            }
            _buildConfig() {
              const t = (this._position =
                  this.positionStrategy || this._createPositionStrategy()),
                i = new FM({
                  direction: this._dir,
                  positionStrategy: t,
                  scrollStrategy: this.scrollStrategy,
                  hasBackdrop: this.hasBackdrop,
                });
              return (
                (this.width || 0 === this.width) && (i.width = this.width),
                (this.height || 0 === this.height) && (i.height = this.height),
                (this.minWidth || 0 === this.minWidth) &&
                  (i.minWidth = this.minWidth),
                (this.minHeight || 0 === this.minHeight) &&
                  (i.minHeight = this.minHeight),
                this.backdropClass && (i.backdropClass = this.backdropClass),
                this.panelClass && (i.panelClass = this.panelClass),
                i
              );
            }
            _updatePositionStrategy(t) {
              const i = this.positions.map((r) => ({
                originX: r.originX,
                originY: r.originY,
                overlayX: r.overlayX,
                overlayY: r.overlayY,
                offsetX: r.offsetX || this.offsetX,
                offsetY: r.offsetY || this.offsetY,
                panelClass: r.panelClass || void 0,
              }));
              return t
                .setOrigin(this._getFlexibleConnectedPositionStrategyOrigin())
                .withPositions(i)
                .withFlexibleDimensions(this.flexibleDimensions)
                .withPush(this.push)
                .withGrowAfterOpen(this.growAfterOpen)
                .withViewportMargin(this.viewportMargin)
                .withLockedPosition(this.lockPosition)
                .withTransformOriginOn(this.transformOriginSelector);
            }
            _createPositionStrategy() {
              const t = this._overlay
                .position()
                .flexibleConnectedTo(
                  this._getFlexibleConnectedPositionStrategyOrigin()
                );
              return this._updatePositionStrategy(t), t;
            }
            _getFlexibleConnectedPositionStrategyOrigin() {
              return this.origin instanceof HM
                ? this.origin.elementRef
                : this.origin;
            }
            _attachOverlay() {
              this._overlayRef
                ? (this._overlayRef.getConfig().hasBackdrop = this.hasBackdrop)
                : this._createOverlay(),
                this._overlayRef.hasAttached() ||
                  this._overlayRef.attach(this._templatePortal),
                this.hasBackdrop
                  ? (this._backdropSubscription = this._overlayRef
                      .backdropClick()
                      .subscribe((t) => {
                        this.backdropClick.emit(t);
                      }))
                  : this._backdropSubscription.unsubscribe(),
                this._positionSubscription.unsubscribe(),
                this.positionChange.observers.length > 0 &&
                  (this._positionSubscription = this._position.positionChanges
                    .pipe(
                      (function F2(n, e = !1) {
                        return Fe((t, i) => {
                          let r = 0;
                          t.subscribe(
                            new De(i, (s) => {
                              const o = n(s, r++);
                              (o || e) && i.next(s), !o && i.complete();
                            })
                          );
                        });
                      })(() => this.positionChange.observers.length > 0)
                    )
                    .subscribe((t) => {
                      this.positionChange.emit(t),
                        0 === this.positionChange.observers.length &&
                          this._positionSubscription.unsubscribe();
                    }));
            }
            _detachOverlay() {
              this._overlayRef && this._overlayRef.detach(),
                this._backdropSubscription.unsubscribe(),
                this._positionSubscription.unsubscribe();
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(Tc), _(Rn), _(Zt), _(jM), _(Nl, 8));
            }),
            (n.ɵdir = x({
              type: n,
              selectors: [
                ["", "cdk-connected-overlay", ""],
                ["", "connected-overlay", ""],
                ["", "cdkConnectedOverlay", ""],
              ],
              inputs: {
                origin: ["cdkConnectedOverlayOrigin", "origin"],
                positions: ["cdkConnectedOverlayPositions", "positions"],
                positionStrategy: [
                  "cdkConnectedOverlayPositionStrategy",
                  "positionStrategy",
                ],
                offsetX: ["cdkConnectedOverlayOffsetX", "offsetX"],
                offsetY: ["cdkConnectedOverlayOffsetY", "offsetY"],
                width: ["cdkConnectedOverlayWidth", "width"],
                height: ["cdkConnectedOverlayHeight", "height"],
                minWidth: ["cdkConnectedOverlayMinWidth", "minWidth"],
                minHeight: ["cdkConnectedOverlayMinHeight", "minHeight"],
                backdropClass: [
                  "cdkConnectedOverlayBackdropClass",
                  "backdropClass",
                ],
                panelClass: ["cdkConnectedOverlayPanelClass", "panelClass"],
                viewportMargin: [
                  "cdkConnectedOverlayViewportMargin",
                  "viewportMargin",
                ],
                scrollStrategy: [
                  "cdkConnectedOverlayScrollStrategy",
                  "scrollStrategy",
                ],
                open: ["cdkConnectedOverlayOpen", "open"],
                disableClose: [
                  "cdkConnectedOverlayDisableClose",
                  "disableClose",
                ],
                transformOriginSelector: [
                  "cdkConnectedOverlayTransformOriginOn",
                  "transformOriginSelector",
                ],
                hasBackdrop: ["cdkConnectedOverlayHasBackdrop", "hasBackdrop"],
                lockPosition: [
                  "cdkConnectedOverlayLockPosition",
                  "lockPosition",
                ],
                flexibleDimensions: [
                  "cdkConnectedOverlayFlexibleDimensions",
                  "flexibleDimensions",
                ],
                growAfterOpen: [
                  "cdkConnectedOverlayGrowAfterOpen",
                  "growAfterOpen",
                ],
                push: ["cdkConnectedOverlayPush", "push"],
              },
              outputs: {
                backdropClick: "backdropClick",
                positionChange: "positionChange",
                attach: "attach",
                detach: "detach",
                overlayKeydown: "overlayKeydown",
                overlayOutsideClick: "overlayOutsideClick",
              },
              exportAs: ["cdkConnectedOverlay"],
              features: [at],
            })),
            n
          );
        })();
      const Y2 = {
        provide: jM,
        deps: [Tc],
        useFactory: function K2(n) {
          return () => n.scrollStrategies.reposition();
        },
      };
      let Z2 = (() => {
        class n {}
        return (
          (n.ɵfac = function (t) {
            return new (t || n)();
          }),
          (n.ɵmod = he({ type: n })),
          (n.ɵinj = ce({ providers: [Tc, Y2], imports: [[Io, k2, TM], TM] })),
          n
        );
      })();
      const Q2 = ["trigger"],
        X2 = ["panel"];
      function J2(n, e) {
        if ((1 & n && (D(0, "span", 8), J(1), E()), 2 & n)) {
          const t = K();
          k(1), Pt(t.placeholder);
        }
      }
      function eU(n, e) {
        if ((1 & n && (D(0, "span", 12), J(1), E()), 2 & n)) {
          const t = K(2);
          k(1), Pt(t.triggerValue);
        }
      }
      function tU(n, e) {
        1 & n && Rt(0, 0, ["*ngSwitchCase", "true"]);
      }
      function nU(n, e) {
        1 & n &&
          (D(0, "span", 9),
          be(1, eU, 2, 1, "span", 10),
          be(2, tU, 1, 0, "ng-content", 11),
          E()),
          2 & n &&
            (F("ngSwitch", !!K().customTrigger), k(2), F("ngSwitchCase", !0));
      }
      function iU(n, e) {
        if (1 & n) {
          const t = _i();
          D(0, "div", 13),
            D(1, "div", 14, 15),
            Z("@transformPanel.done", function (r) {
              return nt(t), K()._panelDoneAnimatingStream.next(r.toState);
            })("keydown", function (r) {
              return nt(t), K()._handleKeydown(r);
            }),
            Rt(3, 1),
            E(),
            E();
        }
        if (2 & n) {
          const t = K();
          F("@transformPanelWrap", void 0),
            k(1),
            Uy("mat-select-panel ", t._getPanelTheme(), ""),
            Od("transform-origin", t._transformOrigin)(
              "font-size",
              t._triggerFontSize,
              "px"
            ),
            F("ngClass", t.panelClass)(
              "@transformPanel",
              t.multiple ? "showing-multiple" : "showing"
            ),
            $e("id", t.id + "-panel")("aria-multiselectable", t.multiple)(
              "aria-label",
              t.ariaLabel || null
            )("aria-labelledby", t._getPanelAriaLabelledby());
        }
      }
      const rU = [[["mat-select-trigger"]], "*"],
        sU = ["mat-select-trigger", "*"],
        $M = {
          transformPanelWrap: hf("transformPanelWrap", [
            Ul("* => void", nL("@transformPanel", [tL()], { optional: !0 })),
          ]),
          transformPanel: hf("transformPanel", [
            Hl(
              "void",
              Di({ transform: "scaleY(0.8)", minWidth: "100%", opacity: 0 })
            ),
            Hl(
              "showing",
              Di({
                opacity: 1,
                minWidth: "calc(100% + 32px)",
                transform: "scaleY(1)",
              })
            ),
            Hl(
              "showing-multiple",
              Di({
                opacity: 1,
                minWidth: "calc(100% + 64px)",
                transform: "scaleY(1)",
              })
            ),
            Ul("void => *", ff("120ms cubic-bezier(0, 0, 0.2, 1)")),
            Ul("* => void", ff("100ms 25ms linear", Di({ opacity: 0 }))),
          ]),
        };
      let zM = 0;
      const qM = new T("mat-select-scroll-strategy"),
        cU = new T("MAT_SELECT_CONFIG"),
        uU = {
          provide: qM,
          deps: [Tc],
          useFactory: function lU(n) {
            return () => n.scrollStrategies.reposition();
          },
        };
      class dU {
        constructor(e, t) {
          (this.source = e), (this.value = t);
        }
      }
      const hU = HD(
          NV(
            RV(
              UD(
                class {
                  constructor(n, e, t, i, r) {
                    (this._elementRef = n),
                      (this._defaultErrorStateMatcher = e),
                      (this._parentForm = t),
                      (this._parentFormGroup = i),
                      (this.ngControl = r);
                  }
                }
              )
            )
          )
        ),
        fU = new T("MatSelectTrigger");
      let pU = (() => {
          class n extends hU {
            constructor(t, i, r, s, o, a, l, c, u, d, h, f, p, g) {
              var y, v, m;
              super(o, s, l, c, d),
                (this._viewportRuler = t),
                (this._changeDetectorRef = i),
                (this._ngZone = r),
                (this._dir = a),
                (this._parentFormField = u),
                (this._liveAnnouncer = p),
                (this._defaultOptions = g),
                (this._panelOpen = !1),
                (this._compareWith = (w, A) => w === A),
                (this._uid = "mat-select-" + zM++),
                (this._triggerAriaLabelledBy = null),
                (this._destroy = new le()),
                (this._onChange = () => {}),
                (this._onTouched = () => {}),
                (this._valueId = "mat-select-value-" + zM++),
                (this._panelDoneAnimatingStream = new le()),
                (this._overlayPanelClass =
                  (null === (y = this._defaultOptions) || void 0 === y
                    ? void 0
                    : y.overlayPanelClass) || ""),
                (this._focused = !1),
                (this.controlType = "mat-select"),
                (this._multiple = !1),
                (this._disableOptionCentering =
                  null !==
                    (m =
                      null === (v = this._defaultOptions) || void 0 === v
                        ? void 0
                        : v.disableOptionCentering) &&
                  void 0 !== m &&
                  m),
                (this.ariaLabel = ""),
                (this.optionSelectionChanges = Wf(() => {
                  const w = this.options;
                  return w
                    ? w.changes.pipe(
                        us(w),
                        ni(() => lr(...w.map((A) => A.onSelectionChange)))
                      )
                    : this._ngZone.onStable.pipe(
                        Un(1),
                        ni(() => this.optionSelectionChanges)
                      );
                })),
                (this.openedChange = new Q()),
                (this._openedStream = this.openedChange.pipe(
                  tn((w) => w),
                  re(() => {})
                )),
                (this._closedStream = this.openedChange.pipe(
                  tn((w) => !w),
                  re(() => {})
                )),
                (this.selectionChange = new Q()),
                (this.valueChange = new Q()),
                this.ngControl && (this.ngControl.valueAccessor = this),
                null != (null == g ? void 0 : g.typeaheadDebounceInterval) &&
                  (this._typeaheadDebounceInterval =
                    g.typeaheadDebounceInterval),
                (this._scrollStrategyFactory = f),
                (this._scrollStrategy = this._scrollStrategyFactory()),
                (this.tabIndex = parseInt(h) || 0),
                (this.id = this.id);
            }
            get focused() {
              return this._focused || this._panelOpen;
            }
            get placeholder() {
              return this._placeholder;
            }
            set placeholder(t) {
              (this._placeholder = t), this.stateChanges.next();
            }
            get required() {
              var t, i, r, s;
              return (
                null !==
                  (s =
                    null !== (t = this._required) && void 0 !== t
                      ? t
                      : null ===
                          (r =
                            null === (i = this.ngControl) || void 0 === i
                              ? void 0
                              : i.control) || void 0 === r
                      ? void 0
                      : r.hasValidator(Al.required)) &&
                void 0 !== s &&
                s
              );
            }
            set required(t) {
              (this._required = je(t)), this.stateChanges.next();
            }
            get multiple() {
              return this._multiple;
            }
            set multiple(t) {
              this._multiple = je(t);
            }
            get disableOptionCentering() {
              return this._disableOptionCentering;
            }
            set disableOptionCentering(t) {
              this._disableOptionCentering = je(t);
            }
            get compareWith() {
              return this._compareWith;
            }
            set compareWith(t) {
              (this._compareWith = t),
                this._selectionModel && this._initializeSelection();
            }
            get value() {
              return this._value;
            }
            set value(t) {
              this._assignValue(t) && this._onChange(t);
            }
            get typeaheadDebounceInterval() {
              return this._typeaheadDebounceInterval;
            }
            set typeaheadDebounceInterval(t) {
              this._typeaheadDebounceInterval = Oh(t);
            }
            get id() {
              return this._id;
            }
            set id(t) {
              (this._id = t || this._uid), this.stateChanges.next();
            }
            ngOnInit() {
              (this._selectionModel = new vC(this.multiple)),
                this.stateChanges.next(),
                this._panelDoneAnimatingStream
                  .pipe(Pw(), Nt(this._destroy))
                  .subscribe(() => this._panelDoneAnimating(this.panelOpen));
            }
            ngAfterContentInit() {
              this._initKeyManager(),
                this._selectionModel.changed
                  .pipe(Nt(this._destroy))
                  .subscribe((t) => {
                    t.added.forEach((i) => i.select()),
                      t.removed.forEach((i) => i.deselect());
                  }),
                this.options.changes
                  .pipe(us(null), Nt(this._destroy))
                  .subscribe(() => {
                    this._resetOptions(), this._initializeSelection();
                  });
            }
            ngDoCheck() {
              const t = this._getTriggerAriaLabelledby(),
                i = this.ngControl;
              if (t !== this._triggerAriaLabelledBy) {
                const r = this._elementRef.nativeElement;
                (this._triggerAriaLabelledBy = t),
                  t
                    ? r.setAttribute("aria-labelledby", t)
                    : r.removeAttribute("aria-labelledby");
              }
              i &&
                (this._previousControl !== i.control &&
                  (void 0 !== this._previousControl &&
                    null !== i.disabled &&
                    i.disabled !== this.disabled &&
                    (this.disabled = i.disabled),
                  (this._previousControl = i.control)),
                this.updateErrorState());
            }
            ngOnChanges(t) {
              t.disabled && this.stateChanges.next(),
                t.typeaheadDebounceInterval &&
                  this._keyManager &&
                  this._keyManager.withTypeAhead(
                    this._typeaheadDebounceInterval
                  );
            }
            ngOnDestroy() {
              this._destroy.next(),
                this._destroy.complete(),
                this.stateChanges.complete();
            }
            toggle() {
              this.panelOpen ? this.close() : this.open();
            }
            open() {
              this._canOpen() &&
                ((this._panelOpen = !0),
                this._keyManager.withHorizontalOrientation(null),
                this._highlightCorrectOption(),
                this._changeDetectorRef.markForCheck());
            }
            close() {
              this._panelOpen &&
                ((this._panelOpen = !1),
                this._keyManager.withHorizontalOrientation(
                  this._isRtl() ? "rtl" : "ltr"
                ),
                this._changeDetectorRef.markForCheck(),
                this._onTouched());
            }
            writeValue(t) {
              this._assignValue(t);
            }
            registerOnChange(t) {
              this._onChange = t;
            }
            registerOnTouched(t) {
              this._onTouched = t;
            }
            setDisabledState(t) {
              (this.disabled = t),
                this._changeDetectorRef.markForCheck(),
                this.stateChanges.next();
            }
            get panelOpen() {
              return this._panelOpen;
            }
            get selected() {
              var t, i;
              return this.multiple
                ? (null === (t = this._selectionModel) || void 0 === t
                    ? void 0
                    : t.selected) || []
                : null === (i = this._selectionModel) || void 0 === i
                ? void 0
                : i.selected[0];
            }
            get triggerValue() {
              if (this.empty) return "";
              if (this._multiple) {
                const t = this._selectionModel.selected.map((i) => i.viewValue);
                return this._isRtl() && t.reverse(), t.join(", ");
              }
              return this._selectionModel.selected[0].viewValue;
            }
            _isRtl() {
              return !!this._dir && "rtl" === this._dir.value;
            }
            _handleKeydown(t) {
              this.disabled ||
                (this.panelOpen
                  ? this._handleOpenKeydown(t)
                  : this._handleClosedKeydown(t));
            }
            _handleClosedKeydown(t) {
              const i = t.keyCode,
                r = 40 === i || 38 === i || 37 === i || 39 === i,
                s = 13 === i || 32 === i,
                o = this._keyManager;
              if (
                (!o.isTyping() && s && !ko(t)) ||
                ((this.multiple || t.altKey) && r)
              )
                t.preventDefault(), this.open();
              else if (!this.multiple) {
                const a = this.selected;
                o.onKeydown(t);
                const l = this.selected;
                l && a !== l && this._liveAnnouncer.announce(l.viewValue, 1e4);
              }
            }
            _handleOpenKeydown(t) {
              const i = this._keyManager,
                r = t.keyCode,
                s = 40 === r || 38 === r,
                o = i.isTyping();
              if (s && t.altKey) t.preventDefault(), this.close();
              else if (o || (13 !== r && 32 !== r) || !i.activeItem || ko(t))
                if (!o && this._multiple && 65 === r && t.ctrlKey) {
                  t.preventDefault();
                  const a = this.options.some(
                    (l) => !l.disabled && !l.selected
                  );
                  this.options.forEach((l) => {
                    l.disabled || (a ? l.select() : l.deselect());
                  });
                } else {
                  const a = i.activeItemIndex;
                  i.onKeydown(t),
                    this._multiple &&
                      s &&
                      t.shiftKey &&
                      i.activeItem &&
                      i.activeItemIndex !== a &&
                      i.activeItem._selectViaInteraction();
                }
              else t.preventDefault(), i.activeItem._selectViaInteraction();
            }
            _onFocus() {
              this.disabled || ((this._focused = !0), this.stateChanges.next());
            }
            _onBlur() {
              (this._focused = !1),
                !this.disabled &&
                  !this.panelOpen &&
                  (this._onTouched(),
                  this._changeDetectorRef.markForCheck(),
                  this.stateChanges.next());
            }
            _onAttached() {
              this._overlayDir.positionChange.pipe(Un(1)).subscribe(() => {
                this._changeDetectorRef.detectChanges(),
                  this._positioningSettled();
              });
            }
            _getPanelTheme() {
              return this._parentFormField
                ? `mat-${this._parentFormField.color}`
                : "";
            }
            get empty() {
              return !this._selectionModel || this._selectionModel.isEmpty();
            }
            _initializeSelection() {
              Promise.resolve().then(() => {
                this.ngControl && (this._value = this.ngControl.value),
                  this._setSelectionByValue(this._value),
                  this.stateChanges.next();
              });
            }
            _setSelectionByValue(t) {
              if (
                (this._selectionModel.selected.forEach((i) =>
                  i.setInactiveStyles()
                ),
                this._selectionModel.clear(),
                this.multiple && t)
              )
                Array.isArray(t),
                  t.forEach((i) => this._selectOptionByValue(i)),
                  this._sortValues();
              else {
                const i = this._selectOptionByValue(t);
                i
                  ? this._keyManager.updateActiveItem(i)
                  : this.panelOpen || this._keyManager.updateActiveItem(-1);
              }
              this._changeDetectorRef.markForCheck();
            }
            _selectOptionByValue(t) {
              const i = this.options.find((r) => {
                if (this._selectionModel.isSelected(r)) return !1;
                try {
                  return null != r.value && this._compareWith(r.value, t);
                } catch (s) {
                  return !1;
                }
              });
              return i && this._selectionModel.select(i), i;
            }
            _assignValue(t) {
              return (
                !!(t !== this._value || (this._multiple && Array.isArray(t))) &&
                (this.options && this._setSelectionByValue(t),
                (this._value = t),
                !0)
              );
            }
            _initKeyManager() {
              (this._keyManager = new VN(this.options)
                .withTypeAhead(this._typeaheadDebounceInterval)
                .withVerticalOrientation()
                .withHorizontalOrientation(this._isRtl() ? "rtl" : "ltr")
                .withHomeAndEnd()
                .withAllowedModifierKeys(["shiftKey"])),
                this._keyManager.tabOut
                  .pipe(Nt(this._destroy))
                  .subscribe(() => {
                    this.panelOpen &&
                      (!this.multiple &&
                        this._keyManager.activeItem &&
                        this._keyManager.activeItem._selectViaInteraction(),
                      this.focus(),
                      this.close());
                  }),
                this._keyManager.change
                  .pipe(Nt(this._destroy))
                  .subscribe(() => {
                    this._panelOpen && this.panel
                      ? this._scrollOptionIntoView(
                          this._keyManager.activeItemIndex || 0
                        )
                      : !this._panelOpen &&
                        !this.multiple &&
                        this._keyManager.activeItem &&
                        this._keyManager.activeItem._selectViaInteraction();
                  });
            }
            _resetOptions() {
              const t = lr(this.options.changes, this._destroy);
              this.optionSelectionChanges.pipe(Nt(t)).subscribe((i) => {
                this._onSelect(i.source, i.isUserInput),
                  i.isUserInput &&
                    !this.multiple &&
                    this._panelOpen &&
                    (this.close(), this.focus());
              }),
                lr(...this.options.map((i) => i._stateChanges))
                  .pipe(Nt(t))
                  .subscribe(() => {
                    this._changeDetectorRef.markForCheck(),
                      this.stateChanges.next();
                  });
            }
            _onSelect(t, i) {
              const r = this._selectionModel.isSelected(t);
              null != t.value || this._multiple
                ? (r !== t.selected &&
                    (t.selected
                      ? this._selectionModel.select(t)
                      : this._selectionModel.deselect(t)),
                  i && this._keyManager.setActiveItem(t),
                  this.multiple && (this._sortValues(), i && this.focus()))
                : (t.deselect(),
                  this._selectionModel.clear(),
                  null != this.value && this._propagateChanges(t.value)),
                r !== this._selectionModel.isSelected(t) &&
                  this._propagateChanges(),
                this.stateChanges.next();
            }
            _sortValues() {
              if (this.multiple) {
                const t = this.options.toArray();
                this._selectionModel.sort((i, r) =>
                  this.sortComparator
                    ? this.sortComparator(i, r, t)
                    : t.indexOf(i) - t.indexOf(r)
                ),
                  this.stateChanges.next();
              }
            }
            _propagateChanges(t) {
              let i = null;
              (i = this.multiple
                ? this.selected.map((r) => r.value)
                : this.selected
                ? this.selected.value
                : t),
                (this._value = i),
                this.valueChange.emit(i),
                this._onChange(i),
                this.selectionChange.emit(this._getChangeEvent(i)),
                this._changeDetectorRef.markForCheck();
            }
            _highlightCorrectOption() {
              this._keyManager &&
                (this.empty
                  ? this._keyManager.setFirstItemActive()
                  : this._keyManager.setActiveItem(
                      this._selectionModel.selected[0]
                    ));
            }
            _canOpen() {
              var t;
              return (
                !this._panelOpen &&
                !this.disabled &&
                (null === (t = this.options) || void 0 === t
                  ? void 0
                  : t.length) > 0
              );
            }
            focus(t) {
              this._elementRef.nativeElement.focus(t);
            }
            _getPanelAriaLabelledby() {
              var t;
              if (this.ariaLabel) return null;
              const i =
                null === (t = this._parentFormField) || void 0 === t
                  ? void 0
                  : t.getLabelId();
              return this.ariaLabelledby
                ? (i ? i + " " : "") + this.ariaLabelledby
                : i;
            }
            _getAriaActiveDescendant() {
              return this.panelOpen &&
                this._keyManager &&
                this._keyManager.activeItem
                ? this._keyManager.activeItem.id
                : null;
            }
            _getTriggerAriaLabelledby() {
              var t;
              if (this.ariaLabel) return null;
              const i =
                null === (t = this._parentFormField) || void 0 === t
                  ? void 0
                  : t.getLabelId();
              let r = (i ? i + " " : "") + this._valueId;
              return this.ariaLabelledby && (r += " " + this.ariaLabelledby), r;
            }
            _panelDoneAnimating(t) {
              this.openedChange.emit(t);
            }
            setDescribedByIds(t) {
              this._ariaDescribedby = t.join(" ");
            }
            onContainerClick() {
              this.focus(), this.open();
            }
            get shouldLabelFloat() {
              return (
                this._panelOpen ||
                !this.empty ||
                (this._focused && !!this._placeholder)
              );
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(
                _(Mp),
                _(vi),
                _(ee),
                _(zf),
                _(Se),
                _(Nl, 8),
                _(Ao, 8),
                _(To, 8),
                _(Dp, 8),
                _(Nn, 10),
                Bi("tabindex"),
                _(qM),
                _(ZN),
                _(cU, 8)
              );
            }),
            (n.ɵdir = x({
              type: n,
              viewQuery: function (t, i) {
                if ((1 & t && (yi(Q2, 5), yi(X2, 5), yi(UM, 5)), 2 & t)) {
                  let r;
                  Te((r = Oe())) && (i.trigger = r.first),
                    Te((r = Oe())) && (i.panel = r.first),
                    Te((r = Oe())) && (i._overlayDir = r.first);
                }
              },
              inputs: {
                panelClass: "panelClass",
                placeholder: "placeholder",
                required: "required",
                multiple: "multiple",
                disableOptionCentering: "disableOptionCentering",
                compareWith: "compareWith",
                value: "value",
                ariaLabel: ["aria-label", "ariaLabel"],
                ariaLabelledby: ["aria-labelledby", "ariaLabelledby"],
                errorStateMatcher: "errorStateMatcher",
                typeaheadDebounceInterval: "typeaheadDebounceInterval",
                sortComparator: "sortComparator",
                id: "id",
              },
              outputs: {
                openedChange: "openedChange",
                _openedStream: "opened",
                _closedStream: "closed",
                selectionChange: "selectionChange",
                valueChange: "valueChange",
              },
              features: [se, at],
            })),
            n
          );
        })(),
        gU = (() => {
          class n extends pU {
            constructor() {
              super(...arguments),
                (this._scrollTop = 0),
                (this._triggerFontSize = 0),
                (this._transformOrigin = "top"),
                (this._offsetY = 0),
                (this._positions = [
                  {
                    originX: "start",
                    originY: "top",
                    overlayX: "start",
                    overlayY: "top",
                  },
                  {
                    originX: "start",
                    originY: "bottom",
                    overlayX: "start",
                    overlayY: "bottom",
                  },
                ]);
            }
            _calculateOverlayScroll(t, i, r) {
              const s = this._getItemHeight();
              return Math.min(Math.max(0, s * t - i + s / 2), r);
            }
            ngOnInit() {
              super.ngOnInit(),
                this._viewportRuler
                  .change()
                  .pipe(Nt(this._destroy))
                  .subscribe(() => {
                    this.panelOpen &&
                      ((this._triggerRect =
                        this.trigger.nativeElement.getBoundingClientRect()),
                      this._changeDetectorRef.markForCheck());
                  });
            }
            open() {
              super._canOpen() &&
                (super.open(),
                (this._triggerRect =
                  this.trigger.nativeElement.getBoundingClientRect()),
                (this._triggerFontSize = parseInt(
                  getComputedStyle(this.trigger.nativeElement).fontSize || "0"
                )),
                this._calculateOverlayPosition(),
                this._ngZone.onStable.pipe(Un(1)).subscribe(() => {
                  this._triggerFontSize &&
                    this._overlayDir.overlayRef &&
                    this._overlayDir.overlayRef.overlayElement &&
                    (this._overlayDir.overlayRef.overlayElement.style.fontSize = `${this._triggerFontSize}px`);
                }));
            }
            _scrollOptionIntoView(t) {
              const i = QD(t, this.options, this.optionGroups),
                r = this._getItemHeight();
              this.panel.nativeElement.scrollTop =
                0 === t && 1 === i
                  ? 0
                  : (function YV(n, e, t, i) {
                      return n < t
                        ? n
                        : n + e > t + i
                        ? Math.max(0, n - i + e)
                        : t;
                    })((t + i) * r, r, this.panel.nativeElement.scrollTop, 256);
            }
            _positioningSettled() {
              this._calculateOverlayOffsetX(),
                (this.panel.nativeElement.scrollTop = this._scrollTop);
            }
            _panelDoneAnimating(t) {
              this.panelOpen
                ? (this._scrollTop = 0)
                : ((this._overlayDir.offsetX = 0),
                  this._changeDetectorRef.markForCheck()),
                super._panelDoneAnimating(t);
            }
            _getChangeEvent(t) {
              return new dU(this, t);
            }
            _calculateOverlayOffsetX() {
              const t =
                  this._overlayDir.overlayRef.overlayElement.getBoundingClientRect(),
                i = this._viewportRuler.getViewportSize(),
                r = this._isRtl(),
                s = this.multiple ? 56 : 32;
              let o;
              if (this.multiple) o = 40;
              else if (this.disableOptionCentering) o = 16;
              else {
                let c = this._selectionModel.selected[0] || this.options.first;
                o = c && c.group ? 32 : 16;
              }
              r || (o *= -1);
              const a = 0 - (t.left + o - (r ? s : 0)),
                l = t.right + o - i.width + (r ? 0 : s);
              a > 0 ? (o += a + 8) : l > 0 && (o -= l + 8),
                (this._overlayDir.offsetX = Math.round(o)),
                this._overlayDir.overlayRef.updatePosition();
            }
            _calculateOverlayOffsetY(t, i, r) {
              const s = this._getItemHeight(),
                o = (s - this._triggerRect.height) / 2,
                a = Math.floor(256 / s);
              let l;
              return this.disableOptionCentering
                ? 0
                : ((l =
                    0 === this._scrollTop
                      ? t * s
                      : this._scrollTop === r
                      ? (t - (this._getItemCount() - a)) * s +
                        (s - ((this._getItemCount() * s - 256) % s))
                      : i - s / 2),
                  Math.round(-1 * l - o));
            }
            _checkOverlayWithinViewport(t) {
              const i = this._getItemHeight(),
                r = this._viewportRuler.getViewportSize(),
                s = this._triggerRect.top - 8,
                o = r.height - this._triggerRect.bottom - 8,
                a = Math.abs(this._offsetY),
                c =
                  Math.min(this._getItemCount() * i, 256) -
                  a -
                  this._triggerRect.height;
              c > o
                ? this._adjustPanelUp(c, o)
                : a > s
                ? this._adjustPanelDown(a, s, t)
                : (this._transformOrigin = this._getOriginBasedOnOption());
            }
            _adjustPanelUp(t, i) {
              const r = Math.round(t - i);
              (this._scrollTop -= r),
                (this._offsetY -= r),
                (this._transformOrigin = this._getOriginBasedOnOption()),
                this._scrollTop <= 0 &&
                  ((this._scrollTop = 0),
                  (this._offsetY = 0),
                  (this._transformOrigin = "50% bottom 0px"));
            }
            _adjustPanelDown(t, i, r) {
              const s = Math.round(t - i);
              if (
                ((this._scrollTop += s),
                (this._offsetY += s),
                (this._transformOrigin = this._getOriginBasedOnOption()),
                this._scrollTop >= r)
              )
                return (
                  (this._scrollTop = r),
                  (this._offsetY = 0),
                  void (this._transformOrigin = "50% top 0px")
                );
            }
            _calculateOverlayPosition() {
              const t = this._getItemHeight(),
                i = this._getItemCount(),
                r = Math.min(i * t, 256),
                o = i * t - r;
              let a;
              (a = this.empty
                ? 0
                : Math.max(
                    this.options
                      .toArray()
                      .indexOf(this._selectionModel.selected[0]),
                    0
                  )),
                (a += QD(a, this.options, this.optionGroups));
              const l = r / 2;
              (this._scrollTop = this._calculateOverlayScroll(a, l, o)),
                (this._offsetY = this._calculateOverlayOffsetY(a, l, o)),
                this._checkOverlayWithinViewport(o);
            }
            _getOriginBasedOnOption() {
              const t = this._getItemHeight(),
                i = (t - this._triggerRect.height) / 2;
              return `50% ${Math.abs(this._offsetY) - i + t / 2}px 0px`;
            }
            _getItemHeight() {
              return 3 * this._triggerFontSize;
            }
            _getItemCount() {
              return this.options.length + this.optionGroups.length;
            }
          }
          return (
            (n.ɵfac = (function () {
              let e;
              return function (i) {
                return (e || (e = gt(n)))(i || n);
              };
            })()),
            (n.ɵcmp = Dn({
              type: n,
              selectors: [["mat-select"]],
              contentQueries: function (t, i, r) {
                if (
                  (1 & t && (ut(r, fU, 5), ut(r, ZD, 5), ut(r, YD, 5)), 2 & t)
                ) {
                  let s;
                  Te((s = Oe())) && (i.customTrigger = s.first),
                    Te((s = Oe())) && (i.options = s),
                    Te((s = Oe())) && (i.optionGroups = s);
                }
              },
              hostAttrs: [
                "role",
                "combobox",
                "aria-autocomplete",
                "none",
                "aria-haspopup",
                "true",
                1,
                "mat-select",
              ],
              hostVars: 20,
              hostBindings: function (t, i) {
                1 & t &&
                  Z("keydown", function (s) {
                    return i._handleKeydown(s);
                  })("focus", function () {
                    return i._onFocus();
                  })("blur", function () {
                    return i._onBlur();
                  }),
                  2 & t &&
                    ($e("id", i.id)("tabindex", i.tabIndex)(
                      "aria-controls",
                      i.panelOpen ? i.id + "-panel" : null
                    )("aria-expanded", i.panelOpen)(
                      "aria-label",
                      i.ariaLabel || null
                    )("aria-required", i.required.toString())(
                      "aria-disabled",
                      i.disabled.toString()
                    )("aria-invalid", i.errorState)(
                      "aria-describedby",
                      i._ariaDescribedby || null
                    )("aria-activedescendant", i._getAriaActiveDescendant()),
                    Dt("mat-select-disabled", i.disabled)(
                      "mat-select-invalid",
                      i.errorState
                    )("mat-select-required", i.required)(
                      "mat-select-empty",
                      i.empty
                    )("mat-select-multiple", i.multiple));
              },
              inputs: {
                disabled: "disabled",
                disableRipple: "disableRipple",
                tabIndex: "tabIndex",
              },
              exportAs: ["matSelect"],
              features: [
                ge([
                  { provide: Ec, useExisting: n },
                  { provide: KD, useExisting: n },
                ]),
                se,
              ],
              ngContentSelectors: sU,
              decls: 9,
              vars: 12,
              consts: [
                ["cdk-overlay-origin", "", 1, "mat-select-trigger", 3, "click"],
                ["origin", "cdkOverlayOrigin", "trigger", ""],
                [1, "mat-select-value", 3, "ngSwitch"],
                [
                  "class",
                  "mat-select-placeholder mat-select-min-line",
                  4,
                  "ngSwitchCase",
                ],
                [
                  "class",
                  "mat-select-value-text",
                  3,
                  "ngSwitch",
                  4,
                  "ngSwitchCase",
                ],
                [1, "mat-select-arrow-wrapper"],
                [1, "mat-select-arrow"],
                [
                  "cdk-connected-overlay",
                  "",
                  "cdkConnectedOverlayLockPosition",
                  "",
                  "cdkConnectedOverlayHasBackdrop",
                  "",
                  "cdkConnectedOverlayBackdropClass",
                  "cdk-overlay-transparent-backdrop",
                  3,
                  "cdkConnectedOverlayPanelClass",
                  "cdkConnectedOverlayScrollStrategy",
                  "cdkConnectedOverlayOrigin",
                  "cdkConnectedOverlayOpen",
                  "cdkConnectedOverlayPositions",
                  "cdkConnectedOverlayMinWidth",
                  "cdkConnectedOverlayOffsetY",
                  "backdropClick",
                  "attach",
                  "detach",
                ],
                [1, "mat-select-placeholder", "mat-select-min-line"],
                [1, "mat-select-value-text", 3, "ngSwitch"],
                ["class", "mat-select-min-line", 4, "ngSwitchDefault"],
                [4, "ngSwitchCase"],
                [1, "mat-select-min-line"],
                [1, "mat-select-panel-wrap"],
                ["role", "listbox", "tabindex", "-1", 3, "ngClass", "keydown"],
                ["panel", ""],
              ],
              template: function (t, i) {
                if (
                  (1 & t &&
                    (eo(rU),
                    D(0, "div", 0, 1),
                    Z("click", function () {
                      return i.toggle();
                    }),
                    D(3, "div", 2),
                    be(4, J2, 2, 1, "span", 3),
                    be(5, nU, 3, 2, "span", 4),
                    E(),
                    D(6, "div", 5),
                    Me(7, "div", 6),
                    E(),
                    E(),
                    be(8, iU, 4, 14, "ng-template", 7),
                    Z("backdropClick", function () {
                      return i.close();
                    })("attach", function () {
                      return i._onAttached();
                    })("detach", function () {
                      return i.close();
                    })),
                  2 & t)
                ) {
                  const r = bd(1);
                  $e("aria-owns", i.panelOpen ? i.id + "-panel" : null),
                    k(3),
                    F("ngSwitch", i.empty),
                    $e("id", i._valueId),
                    k(1),
                    F("ngSwitchCase", !0),
                    k(1),
                    F("ngSwitchCase", !1),
                    k(3),
                    F("cdkConnectedOverlayPanelClass", i._overlayPanelClass)(
                      "cdkConnectedOverlayScrollStrategy",
                      i._scrollStrategy
                    )("cdkConnectedOverlayOrigin", r)(
                      "cdkConnectedOverlayOpen",
                      i.panelOpen
                    )("cdkConnectedOverlayPositions", i._positions)(
                      "cdkConnectedOverlayMinWidth",
                      null == i._triggerRect ? null : i._triggerRect.width
                    )("cdkConnectedOverlayOffsetY", i._offsetY);
                }
              },
              directives: [HM, vo, bh, Jb, UM, Zb],
              styles: [
                '.mat-select{display:inline-block;width:100%;outline:none}.mat-select-trigger{display:inline-flex;align-items:center;cursor:pointer;position:relative;box-sizing:border-box;width:100%}.mat-select-disabled .mat-select-trigger{-webkit-user-select:none;user-select:none;cursor:default}.mat-select-value{width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.mat-select-value-text{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.mat-select-arrow-wrapper{height:16px;flex-shrink:0;display:inline-flex;align-items:center}.mat-form-field-appearance-fill .mat-select-arrow-wrapper{transform:translateY(-50%)}.mat-form-field-appearance-outline .mat-select-arrow-wrapper{transform:translateY(-25%)}.mat-form-field-appearance-standard.mat-form-field-has-label .mat-select:not(.mat-select-empty) .mat-select-arrow-wrapper{transform:translateY(-50%)}.mat-form-field-appearance-standard .mat-select.mat-select-empty .mat-select-arrow-wrapper{transition:transform 400ms cubic-bezier(0.25, 0.8, 0.25, 1)}._mat-animation-noopable.mat-form-field-appearance-standard .mat-select.mat-select-empty .mat-select-arrow-wrapper{transition:none}.mat-select-arrow{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:5px solid;margin:0 4px}.mat-form-field.mat-focused .mat-select-arrow{transform:translateX(0)}.mat-select-panel-wrap{flex-basis:100%}.mat-select-panel{min-width:112px;max-width:280px;overflow:auto;-webkit-overflow-scrolling:touch;padding-top:0;padding-bottom:0;max-height:256px;min-width:100%;border-radius:4px;outline:0}.cdk-high-contrast-active .mat-select-panel{outline:solid 1px}.mat-select-panel .mat-optgroup-label,.mat-select-panel .mat-option{font-size:inherit;line-height:3em;height:3em}.mat-form-field-type-mat-select:not(.mat-form-field-disabled) .mat-form-field-flex{cursor:pointer}.mat-form-field-type-mat-select .mat-form-field-label{width:calc(100% - 18px)}.mat-select-placeholder{transition:color 400ms 133.3333333333ms cubic-bezier(0.25, 0.8, 0.25, 1)}._mat-animation-noopable .mat-select-placeholder{transition:none}.mat-form-field-hide-placeholder .mat-select-placeholder{color:transparent;-webkit-text-fill-color:transparent;transition:none;display:block}.mat-select-min-line:empty::before{content:" ";white-space:pre;width:1px;display:inline-block;visibility:hidden}\n',
              ],
              encapsulation: 2,
              data: { animation: [$M.transformPanelWrap, $M.transformPanel] },
              changeDetection: 0,
            })),
            n
          );
        })(),
        mU = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({
              providers: [uU],
              imports: [[bl, Z2, XD, bn], Sp, Mc, XD, bn],
            })),
            n
          );
        })();
      const WM = Ll({ passive: !0 });
      let _U = (() => {
          class n {
            constructor(t, i) {
              (this._platform = t),
                (this._ngZone = i),
                (this._monitoredElements = new Map());
            }
            monitor(t) {
              if (!this._platform.isBrowser) return wn;
              const i = ei(t),
                r = this._monitoredElements.get(i);
              if (r) return r.subject;
              const s = new le(),
                o = "cdk-text-field-autofilled",
                a = (l) => {
                  "cdk-text-field-autofill-start" !== l.animationName ||
                  i.classList.contains(o)
                    ? "cdk-text-field-autofill-end" === l.animationName &&
                      i.classList.contains(o) &&
                      (i.classList.remove(o),
                      this._ngZone.run(() =>
                        s.next({ target: l.target, isAutofilled: !1 })
                      ))
                    : (i.classList.add(o),
                      this._ngZone.run(() =>
                        s.next({ target: l.target, isAutofilled: !0 })
                      ));
                };
              return (
                this._ngZone.runOutsideAngular(() => {
                  i.addEventListener("animationstart", a, WM),
                    i.classList.add("cdk-text-field-autofill-monitored");
                }),
                this._monitoredElements.set(i, {
                  subject: s,
                  unlisten: () => {
                    i.removeEventListener("animationstart", a, WM);
                  },
                }),
                s
              );
            }
            stopMonitoring(t) {
              const i = ei(t),
                r = this._monitoredElements.get(i);
              r &&
                (r.unlisten(),
                r.subject.complete(),
                i.classList.remove("cdk-text-field-autofill-monitored"),
                i.classList.remove("cdk-text-field-autofilled"),
                this._monitoredElements.delete(i));
            }
            ngOnDestroy() {
              this._monitoredElements.forEach((t, i) => this.stopMonitoring(i));
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(b(Jt), b(ee));
            }),
            (n.ɵprov = I({ token: n, factory: n.ɵfac, providedIn: "root" })),
            n
          );
        })(),
        KM = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({})),
            n
          );
        })();
      const yU = new T("MAT_INPUT_VALUE_ACCESSOR"),
        vU = [
          "button",
          "checkbox",
          "file",
          "hidden",
          "image",
          "radio",
          "range",
          "reset",
          "submit",
        ];
      let bU = 0;
      const CU = UD(
        class {
          constructor(n, e, t, i) {
            (this._defaultErrorStateMatcher = n),
              (this._parentForm = e),
              (this._parentFormGroup = t),
              (this.ngControl = i);
          }
        }
      );
      let wU = (() => {
          class n extends CU {
            constructor(t, i, r, s, o, a, l, c, u, d) {
              super(a, s, o, r),
                (this._elementRef = t),
                (this._platform = i),
                (this._autofillMonitor = c),
                (this._formField = d),
                (this._uid = "mat-input-" + bU++),
                (this.focused = !1),
                (this.stateChanges = new le()),
                (this.controlType = "mat-input"),
                (this.autofilled = !1),
                (this._disabled = !1),
                (this._type = "text"),
                (this._readonly = !1),
                (this._neverEmptyInputTypes = [
                  "date",
                  "datetime",
                  "datetime-local",
                  "month",
                  "time",
                  "week",
                ].filter((p) => Aw().has(p))),
                (this._iOSKeyupListener = (p) => {
                  const g = p.target;
                  !g.value &&
                    0 === g.selectionStart &&
                    0 === g.selectionEnd &&
                    (g.setSelectionRange(1, 1), g.setSelectionRange(0, 0));
                });
              const h = this._elementRef.nativeElement,
                f = h.nodeName.toLowerCase();
              (this._inputValueAccessor = l || h),
                (this._previousNativeValue = this.value),
                (this.id = this.id),
                i.IOS &&
                  u.runOutsideAngular(() => {
                    t.nativeElement.addEventListener(
                      "keyup",
                      this._iOSKeyupListener
                    );
                  }),
                (this._isServer = !this._platform.isBrowser),
                (this._isNativeSelect = "select" === f),
                (this._isTextarea = "textarea" === f),
                (this._isInFormField = !!d),
                this._isNativeSelect &&
                  (this.controlType = h.multiple
                    ? "mat-native-select-multiple"
                    : "mat-native-select");
            }
            get disabled() {
              return this.ngControl && null !== this.ngControl.disabled
                ? this.ngControl.disabled
                : this._disabled;
            }
            set disabled(t) {
              (this._disabled = je(t)),
                this.focused && ((this.focused = !1), this.stateChanges.next());
            }
            get id() {
              return this._id;
            }
            set id(t) {
              this._id = t || this._uid;
            }
            get required() {
              var t, i, r, s;
              return (
                null !==
                  (s =
                    null !== (t = this._required) && void 0 !== t
                      ? t
                      : null ===
                          (r =
                            null === (i = this.ngControl) || void 0 === i
                              ? void 0
                              : i.control) || void 0 === r
                      ? void 0
                      : r.hasValidator(Al.required)) &&
                void 0 !== s &&
                s
              );
            }
            set required(t) {
              this._required = je(t);
            }
            get type() {
              return this._type;
            }
            set type(t) {
              (this._type = t || "text"),
                this._validateType(),
                !this._isTextarea &&
                  Aw().has(this._type) &&
                  (this._elementRef.nativeElement.type = this._type);
            }
            get value() {
              return this._inputValueAccessor.value;
            }
            set value(t) {
              t !== this.value &&
                ((this._inputValueAccessor.value = t),
                this.stateChanges.next());
            }
            get readonly() {
              return this._readonly;
            }
            set readonly(t) {
              this._readonly = je(t);
            }
            ngAfterViewInit() {
              this._platform.isBrowser &&
                this._autofillMonitor
                  .monitor(this._elementRef.nativeElement)
                  .subscribe((t) => {
                    (this.autofilled = t.isAutofilled),
                      this.stateChanges.next();
                  });
            }
            ngOnChanges() {
              this.stateChanges.next();
            }
            ngOnDestroy() {
              this.stateChanges.complete(),
                this._platform.isBrowser &&
                  this._autofillMonitor.stopMonitoring(
                    this._elementRef.nativeElement
                  ),
                this._platform.IOS &&
                  this._elementRef.nativeElement.removeEventListener(
                    "keyup",
                    this._iOSKeyupListener
                  );
            }
            ngDoCheck() {
              this.ngControl && this.updateErrorState(),
                this._dirtyCheckNativeValue(),
                this._dirtyCheckPlaceholder();
            }
            focus(t) {
              this._elementRef.nativeElement.focus(t);
            }
            _focusChanged(t) {
              t !== this.focused &&
                ((this.focused = t), this.stateChanges.next());
            }
            _onInput() {}
            _dirtyCheckPlaceholder() {
              var t, i;
              const r = (
                null ===
                  (i =
                    null === (t = this._formField) || void 0 === t
                      ? void 0
                      : t._hideControlPlaceholder) || void 0 === i
                  ? void 0
                  : i.call(t)
              )
                ? null
                : this.placeholder;
              if (r !== this._previousPlaceholder) {
                const s = this._elementRef.nativeElement;
                (this._previousPlaceholder = r),
                  r
                    ? s.setAttribute("placeholder", r)
                    : s.removeAttribute("placeholder");
              }
            }
            _dirtyCheckNativeValue() {
              const t = this._elementRef.nativeElement.value;
              this._previousNativeValue !== t &&
                ((this._previousNativeValue = t), this.stateChanges.next());
            }
            _validateType() {
              vU.indexOf(this._type);
            }
            _isNeverEmpty() {
              return this._neverEmptyInputTypes.indexOf(this._type) > -1;
            }
            _isBadInput() {
              let t = this._elementRef.nativeElement.validity;
              return t && t.badInput;
            }
            get empty() {
              return !(
                this._isNeverEmpty() ||
                this._elementRef.nativeElement.value ||
                this._isBadInput() ||
                this.autofilled
              );
            }
            get shouldLabelFloat() {
              if (this._isNativeSelect) {
                const t = this._elementRef.nativeElement,
                  i = t.options[0];
                return (
                  this.focused ||
                  t.multiple ||
                  !this.empty ||
                  !!(t.selectedIndex > -1 && i && i.label)
                );
              }
              return this.focused || !this.empty;
            }
            setDescribedByIds(t) {
              t.length
                ? this._elementRef.nativeElement.setAttribute(
                    "aria-describedby",
                    t.join(" ")
                  )
                : this._elementRef.nativeElement.removeAttribute(
                    "aria-describedby"
                  );
            }
            onContainerClick() {
              this.focused || this.focus();
            }
            _isInlineSelect() {
              const t = this._elementRef.nativeElement;
              return this._isNativeSelect && (t.multiple || t.size > 1);
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(
                _(Se),
                _(Jt),
                _(Nn, 10),
                _(Ao, 8),
                _(To, 8),
                _(zf),
                _(yU, 10),
                _(_U),
                _(ee),
                _(Dp, 8)
              );
            }),
            (n.ɵdir = x({
              type: n,
              selectors: [
                ["input", "matInput", ""],
                ["textarea", "matInput", ""],
                ["select", "matNativeControl", ""],
                ["input", "matNativeControl", ""],
                ["textarea", "matNativeControl", ""],
              ],
              hostAttrs: [
                1,
                "mat-input-element",
                "mat-form-field-autofill-control",
              ],
              hostVars: 12,
              hostBindings: function (t, i) {
                1 & t &&
                  Z("focus", function () {
                    return i._focusChanged(!0);
                  })("blur", function () {
                    return i._focusChanged(!1);
                  })("input", function () {
                    return i._onInput();
                  }),
                  2 & t &&
                    (Wa("disabled", i.disabled)("required", i.required),
                    $e("id", i.id)("data-placeholder", i.placeholder)(
                      "name",
                      i.name || null
                    )("readonly", (i.readonly && !i._isNativeSelect) || null)(
                      "aria-invalid",
                      i.empty && i.required ? null : i.errorState
                    )("aria-required", i.required),
                    Dt("mat-input-server", i._isServer)(
                      "mat-native-select-inline",
                      i._isInlineSelect()
                    ));
              },
              inputs: {
                disabled: "disabled",
                id: "id",
                placeholder: "placeholder",
                name: "name",
                required: "required",
                type: "type",
                errorStateMatcher: "errorStateMatcher",
                userAriaDescribedBy: [
                  "aria-describedby",
                  "userAriaDescribedBy",
                ],
                value: "value",
                readonly: "readonly",
              },
              exportAs: ["matInput"],
              features: [ge([{ provide: Ec, useExisting: n }]), se, at],
            })),
            n
          );
        })(),
        DU = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n })),
            (n.ɵinj = ce({ providers: [zf], imports: [[KM, Mc, bn], KM, Mc] })),
            n
          );
        })();
      function EU(n, e) {
        if ((1 & n && (D(0, "div", 10), Me(1, "img", 11), E()), 2 & n)) {
          const t = K();
          k(1), F("src", t.liveFeedUrlLeft, Ar);
        }
      }
      function MU(n, e) {
        if ((1 & n && (D(0, "div", 10), Me(1, "img", 12), E()), 2 & n)) {
          const t = K();
          k(1), F("src", t.liveFeedUrlRight, Ar);
        }
      }
      function SU(n, e) {
        if (1 & n) {
          const t = _i();
          D(0, "div", 13),
            Me(1, "img", 14),
            D(2, "mat-button-toggle", 15),
            Z("click", function () {
              return nt(t), K().toggleManualMode();
            }),
            J(3),
            E(),
            D(4, "mat-button-toggle", 15),
            Z("click", function () {
              return nt(t), K().moveToCenter();
            }),
            J(5),
            E(),
            E();
        }
        if (2 & n) {
          const t = K();
          k(3),
            Pt(t.manualEnabled ? "Disable Manual-Mode" : "Enable Manual-Mode"),
            k(2),
            Pt("Center");
        }
      }
      function AU(n, e) {
        if (1 & n) {
          const t = _i();
          D(0, "div", 16),
            D(1, "div", 17),
            D(2, "mat-form-field"),
            D(3, "mat-label"),
            J(4, "Select Left Camera "),
            E(),
            D(5, "mat-select", 18),
            Z("valueChange", function (r) {
              return nt(t), (K().leftCamera = r);
            }),
            D(6, "mat-option", 19),
            J(7, "Camera 1"),
            E(),
            D(8, "mat-option", 20),
            J(9, "Camera 2"),
            E(),
            E(),
            E(),
            D(10, "mat-form-field"),
            D(11, "mat-label"),
            J(12, "Select Right Camera "),
            E(),
            D(13, "mat-select", 18),
            Z("valueChange", function (r) {
              return nt(t), (K().rightCamera = r);
            }),
            D(14, "mat-option", 19),
            J(15, "Camera 1"),
            E(),
            D(16, "mat-option", 20),
            J(17, "Camera 2"),
            E(),
            E(),
            E(),
            E(),
            D(18, "div", 21),
            D(19, "div", 22),
            D(20, "mat-form-field"),
            D(21, "mat-label"),
            J(22, "Select DLC node (optional)"),
            E(),
            D(23, "input", 23),
            Z("ngModelChange", function () {
              return nt(t), K().sendNodeIndex();
            }),
            E(),
            E(),
            E(),
            Me(24, "div", 24),
            E(),
            D(25, "div", 21),
            D(26, "mat-button-toggle", 25),
            Z("click", function () {
              return nt(t), K().toggleLiveFeed();
            }),
            J(27),
            E(),
            E(),
            E();
        }
        if (2 & n) {
          const t = K();
          k(5),
            F("value", t.leftCamera)("disabled", t.isLiveFeedEnabled),
            k(8),
            F("value", t.rightCamera)("disabled", t.isLiveFeedEnabled),
            k(10),
            F("formControl", t.nodeIndex)("disabled", t.isLiveFeedEnabled),
            k(4),
            Pt(t.isLiveFeedEnabled ? "Stop Live Feed" : "Start Live Feed");
        }
      }
      function TU(n, e) {
        if (1 & n) {
          const t = _i();
          D(0, "div", 26),
            D(1, "mat-form-field"),
            D(2, "mat-label"),
            J(3, "Select Tracking Algorithm "),
            E(),
            D(4, "mat-select", 18),
            Z("valueChange", function (r) {
              return nt(t), (K().trackingAlgorithm = r);
            }),
            D(5, "mat-option", 27),
            J(6, "Threshold Bright Tracking"),
            E(),
            D(7, "mat-option", 19),
            J(8, "Fluorescent Marker Tracking"),
            E(),
            D(9, "mat-option", 20),
            J(10, "DeepLabCut Tracking"),
            E(),
            E(),
            E(),
            D(11, "div", 28),
            D(12, "mat-button-toggle", 29),
            Z("click", function () {
              return nt(t), K().toggleAutofocus();
            }),
            J(13),
            E(),
            D(14, "mat-button-toggle", 29),
            Z("click", function () {
              return nt(t), K().toggleTracking();
            }),
            J(15),
            E(),
            D(16, "mat-button-toggle", 15),
            Z("click", function () {
              return nt(t), K().toggleHeatmap();
            }),
            J(17),
            E(),
            E(),
            E();
        }
        if (2 & n) {
          const t = K();
          k(4),
            F("value", t.trackingAlgorithm)("disabled", t.isTrackingEnabled),
            k(9),
            Pt(t.isAutofocusEnabled ? "Disable FocusLock" : "Enable FocusLock"),
            k(2),
            Pt(t.isTrackingEnabled ? "Disable Tracking" : "Enable Tracking"),
            k(2),
            Pt(t.heatmapOn ? "Disable Heatmap" : "Enable Heatmap");
        }
      }
      function OU(n, e) {
        if (1 & n) {
          const t = _i();
          D(0, "div", 13),
            D(1, "div", 30),
            D(2, "mat-form-field"),
            D(3, "mat-label"),
            J(4, "Directory Path"),
            E(),
            Me(5, "input", 31),
            E(),
            D(6, "mat-form-field"),
            D(7, "mat-label"),
            J(8, "Filename"),
            E(),
            Me(9, "input", 32),
            E(),
            D(10, "div", 33),
            D(11, "p"),
            J(12, "Left File Type:"),
            E(),
            D(13, "mat-button-toggle-group", 34),
            Z("valueChange", function (r) {
              return nt(t), (K().useAviLeft = r);
            }),
            D(14, "mat-button-toggle", 35),
            J(15, ".avi"),
            E(),
            D(16, "mat-button-toggle", 35),
            J(17, ".tiff"),
            E(),
            E(),
            E(),
            D(18, "div", 33),
            D(19, "p"),
            J(20, "Right File Type:"),
            E(),
            D(21, "mat-button-toggle-group", 36),
            Z("valueChange", function (r) {
              return nt(t), (K().useAviRight = r);
            }),
            D(22, "mat-button-toggle", 35),
            J(23, ".avi"),
            E(),
            D(24, "mat-button-toggle", 35),
            J(25, ".tiff"),
            E(),
            E(),
            E(),
            E(),
            D(26, "mat-button-toggle", 15),
            Z("click", function () {
              return nt(t), K().toggleRecording();
            }),
            J(27),
            E(),
            E();
        }
        if (2 & n) {
          const t = K();
          k(5),
            F("formControl", t.folder),
            k(4),
            F("formControl", t.filename),
            k(4),
            F("value", t.useAviLeft),
            k(1),
            F("value", 1),
            k(2),
            F("value", 0),
            k(5),
            F("value", t.useAviRight),
            k(1),
            F("value", 1),
            k(2),
            F("value", 0),
            k(3),
            Pt(t.isRecording ? "Stop Recording" : "Start Recording");
        }
      }
      function IU(n, e) {
        if (
          (1 & n &&
            (D(0, "div", 13),
            D(1, "div", 37),
            Me(2, "img", 38),
            E(),
            D(3, "p", 39),
            J(4),
            E(),
            E()),
          2 & n)
        ) {
          const t = K();
          k(2),
            F("src", t.liveFeedUrlHistogram, Ar),
            k(2),
            no(" ", t.hist_max_feed, " ");
        }
      }
      let xU = (() => {
          class n {
            constructor(t, i) {
              (this.http = t),
                (this.sockService = i),
                (this.isLiveFeedEnabled = !1),
                (this.isRecording = !1),
                (this.heatmapOn = !1),
                (this.manualEnabled = !1),
                (this.isTrackingEnabled = !1),
                (this.isAutofocusEnabled = !1),
                (this.apiUrl = "http://127.0.0.1:5000"),
                (this.hist_max_feed = "0"),
                (this.indexMin = 0),
                (this.indexMax = 2),
                (this.recordingSettings = {
                  filepath: "D:\\WormSpy_video\\",
                  filename: "Tracking_Video",
                  use_avi_left: 0,
                  use_avi_right: 0,
                }),
                (this.serialInput = new rs("COM4")),
                (this.nodeIndex = new rs("0", [
                  Al.min(this.indexMin),
                  Al.max(this.indexMax),
                ])),
                (this.leftCamera = "1"),
                (this.rightCamera = "2"),
                (this.folder = new rs("D:\\WormSpy_Video\\")),
                (this.filename = new rs("Project_1")),
                (this.trackingAlgorithm = 0),
                (this.useAviLeft = 1),
                (this.useAviRight = 1);
            }
            ngOnInit() {}
            toggleLiveFeed() {
              this.isLiveFeedEnabled = !this.isLiveFeedEnabled;
              const t = {
                leftCam: this.selectToCamera(this.leftCamera),
                rightCam: this.selectToCamera(this.rightCamera),
                serialInput: this.serialInput.value,
              };
              this.isLiveFeedEnabled
                ? (this.serialInput.disable(),
                  this.http
                    .post(this.apiUrl + "/camera_settings", t)
                    .subscribe(() => {
                      (this.liveFeedUrlLeft = this.apiUrl + "/video_feed"),
                        (this.liveFeedUrlRight =
                          this.apiUrl + "/video_feed_fluorescent"),
                        (this.liveFeedUrlHistogram = this.apiUrl + "/get_hist"),
                        (this.hist_max_feed = this.apiUrl + "/stream_max");
                    }))
                : (this.serialInput.enable(),
                  (this.liveFeedUrlLeft = ""),
                  (this.liveFeedUrlRight = ""),
                  (this.liveFeedUrlHistogram = ""),
                  this.http
                    .post(this.apiUrl + "/stop_live_stream", {})
                    .subscribe(() => {}));
            }
            toggleRecording() {
              (this.isRecording = !this.isRecording),
                this.isRecording
                  ? (this.filename.disable(),
                    (this.recordingSettings.filepath = this.folder.value),
                    (this.recordingSettings.filename = this.filename.value),
                    (this.recordingSettings.use_avi_left = this.useAviLeft),
                    (this.recordingSettings.use_avi_right = this.useAviRight),
                    this.http
                      .post(
                        this.apiUrl + "/start_recording",
                        this.recordingSettings
                      )
                      .subscribe(() => {}))
                  : (this.http
                      .post(this.apiUrl + "/stop_recording", {})
                      .subscribe(() => {}),
                    this.filename.enable());
            }
            toggleHeatmap() {
              (this.heatmapOn = !this.heatmapOn),
                this.heatmapOn
                  ? this.http
                      .post(this.apiUrl + "/toggle_heatmap", {
                        heatmap_enabled: "True",
                      })
                      .subscribe(() => {})
                  : this.http
                      .post(this.apiUrl + "/toggle_heatmap", {
                        heatmap_enabled: "False",
                      })
                      .subscribe(() => {});
            }
            toggleTracking() {
              (this.isTrackingEnabled = !this.isTrackingEnabled),
                this.isTrackingEnabled
                  ? this.http
                      .post(this.apiUrl + "/toggle_tracking", {
                        is_tracking: "True",
                        tracking_algorithm: this.trackingAlgorithm,
                      })
                      .subscribe(() => {})
                  : this.http
                      .post(this.apiUrl + "/toggle_tracking", {
                        is_tracking: "False",
                        tracking_algorithm: this.trackingAlgorithm,
                      })
                      .subscribe(() => {});
            }
            sendNodeIndex() {
              if ("" !== this.nodeIndex.value && null != this.nodeIndex.value) {
                let t = parseInt(this.nodeIndex.value);
                0 == parseInt(this.nodeIndex.value) && (t = 0),
                  t > this.indexMax
                    ? (t = this.indexMax)
                    : t < this.indexMin && (t = this.indexMin),
                  this.http
                    .post(this.apiUrl + "/node_index", { index: t })
                    .subscribe(() => {});
              }
            }
            toggleAutofocus() {
              this.isAutofocusEnabled
                ? this.http
                    .post(this.apiUrl + "/toggle_af", { af_enabled: "True" })
                    .subscribe(() => {})
                : this.http
                    .post(this.apiUrl + "/toggle_af", { af_enabled: "False" })
                    .subscribe(() => {}),
                (this.isAutofocusEnabled = !this.isAutofocusEnabled);
            }
            toggleManualMode() {
              (this.manualEnabled = !this.manualEnabled),
                this.manualEnabled
                  ? this.http
                      .post(this.apiUrl + "/toggle_manual", {
                        toggle_manual: "True",
                      })
                      .subscribe(() => {})
                  : this.http
                      .post(this.apiUrl + "/toggle_manual", {
                        toggle_manual: "False",
                      })
                      .subscribe(() => {});
            }
            moveToCenter() {
              this.http
                .post(this.apiUrl + "/move_to_center", {})
                .subscribe(() => {});
            }
            selectToCamera(t) {
              return "4" == t ? 3 : "3" == t ? 2 : "2" == t ? 1 : 0;
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)(_(_M), _(OH));
            }),
            (n.ɵcmp = Dn({
              type: n,
              selectors: [["app-live-feed"]],
              decls: 16,
              vars: 7,
              consts: [
                [1, "main"],
                [2, "font-size", "medium"],
                [1, "background"],
                [1, "live-feed-block"],
                [1, "live-feed-container"],
                ["class", "live-feed", 4, "ngIf"],
                [1, "floating-island"],
                ["class", "recording-settings", 4, "ngIf"],
                ["class", "live-feed-settings", 4, "ngIf"],
                ["class", "function-settings", 4, "ngIf"],
                [1, "live-feed"],
                ["alt", "", 3, "src"],
                ["id", "cam2", "alt", "", 3, "src"],
                [1, "recording-settings"],
                [
                  "src",
                  "{{url_for('static', filename='assets/images/Controller.png')}}",
                  "alt",
                  "",
                  "id",
                  "keyboard",
                ],
                [1, "toggle_button", 3, "click"],
                [1, "live-feed-settings"],
                [1, "top-row-feed-settings"],
                [3, "value", "disabled", "valueChange"],
                ["value", "1"],
                ["value", "2"],
                [1, "bottom-row-feed-settings"],
                [1, "bottom-row-left-feed-settings"],
                [
                  "matInput",
                  "",
                  "type",
                  "number",
                  3,
                  "formControl",
                  "disabled",
                  "ngModelChange",
                ],
                [1, "bottom-row-right-feed-settings"],
                ["id", "livestream-toggle", 3, "click"],
                [1, "function-settings"],
                ["value", "0"],
                [1, "buttons"],
                [3, "click"],
                [1, "camera-settings"],
                [
                  "matInput",
                  "",
                  "type",
                  "text",
                  "placeholder",
                  "C:/user/steve/documents/wormspy/",
                  3,
                  "formControl",
                ],
                [
                  "matInput",
                  "",
                  "type",
                  "text",
                  "placeholder",
                  "recording1",
                  3,
                  "formControl",
                ],
                [1, "avi-div"],
                [
                  "name",
                  "left_filetype",
                  "aria-label",
                  "File Type",
                  3,
                  "value",
                  "valueChange",
                ],
                [3, "value"],
                [
                  "name",
                  "right_filetype",
                  "aria-label",
                  "File Type",
                  3,
                  "value",
                  "valueChange",
                ],
                [1, "hist-feed"],
                ["alt", "", "id", "hist", 3, "src"],
                ["id", "hist_max"],
              ],
              template: function (t, i) {
                1 & t &&
                  (D(0, "div", 0),
                  D(1, "h1"),
                  J(2, "WormsPy "),
                  D(3, "a", 1),
                  J(4, "beta v2.0"),
                  E(),
                  E(),
                  D(5, "div", 2),
                  D(6, "div", 3),
                  D(7, "div", 4),
                  be(8, EU, 2, 1, "div", 5),
                  be(9, MU, 2, 1, "div", 5),
                  E(),
                  D(10, "div", 6),
                  be(11, SU, 6, 2, "div", 7),
                  be(12, AU, 28, 7, "div", 8),
                  be(13, TU, 18, 5, "div", 9),
                  be(14, OU, 28, 9, "div", 7),
                  be(15, IU, 5, 2, "div", 7),
                  E(),
                  E(),
                  E(),
                  E()),
                  2 & t &&
                    (k(8),
                    F("ngIf", i.isLiveFeedEnabled),
                    k(1),
                    F("ngIf", i.isLiveFeedEnabled),
                    k(2),
                    F("ngIf", i.isLiveFeedEnabled),
                    k(1),
                    F("ngIf", !i.isLiveFeedEnabled),
                    k(1),
                    F("ngIf", i.isLiveFeedEnabled),
                    k(1),
                    F("ngIf", i.isLiveFeedEnabled),
                    k(1),
                    F("ngIf", i.isLiveFeedEnabled));
              },
              directives: [vl, rE, d2, wp, gU, ZD, wU, qh, Sl, WC, Kh, iE],
              styles: [
                "h1[_ngcontent-%COMP%]{margin-top:.5%;padding-top:.5%;padding-left:.5%;font-weight:500;font-size:45px;font-family:Roboto,sans-serif;color:#0f0}.background[_ngcontent-%COMP%]{display:flex;flex-direction:row}.main[_ngcontent-%COMP%]{margin-left:auto;margin-right:auto;max-width:100vw}.live-feed-block[_ngcontent-%COMP%]{width:100%;display:flex;flex-direction:column}.live-feed-block[_ngcontent-%COMP%]   .live-feed-container[_ngcontent-%COMP%]{display:flex;flex-direction:row}.live-feed-block[_ngcontent-%COMP%]   .live-feed-container[_ngcontent-%COMP%]   .live-feed[_ngcontent-%COMP%]{width:50%;display:inline-block;margin:5px;border:1px solid #ccc}.live-feed-block[_ngcontent-%COMP%]   .live-feed-container[_ngcontent-%COMP%]   .live-feed[_ngcontent-%COMP%]   img[_ngcontent-%COMP%]{width:100%}.live-feed-block[_ngcontent-%COMP%]   .top-row-feed-settings-live[_ngcontent-%COMP%]{width:100%;display:flex;flex-direction:row}.live-feed-block[_ngcontent-%COMP%]   .top-row-feed-settings-live[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]{width:50%;padding:5px;margin:5px;background-color:#d3d3d3;color:#673ab7;border-color:#673ab7}.live-feed-block[_ngcontent-%COMP%]   .top-row-feed-settings-live[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]:active{background-color:#673ab7;color:#fff}.live-feed-block[_ngcontent-%COMP%]   .top-row-feed-settings-live[_ngcontent-%COMP%]   mat-form-field[_ngcontent-%COMP%]{width:50%;height:30px;margin-right:2%}.live-feed-block[_ngcontent-%COMP%]   .top-row-feed-settings-live[_ngcontent-%COMP%]   mat-form-field[_ngcontent-%COMP%]   mat-label[_ngcontent-%COMP%]{color:#000;font-size:18px}.live-feed-block[_ngcontent-%COMP%]   #keyboard[_ngcontent-%COMP%]{height:200px;padding-left:5px;padding-right:2px;margin-left:auto;margin-right:auto}.live-feed-block[_ngcontent-%COMP%]   .bottom-row-feed-settings-live[_ngcontent-%COMP%]{width:100%;display:flex;flex-direction:row}.live-feed-block[_ngcontent-%COMP%]   .bottom-row-feed-settings-live[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]{width:50%;padding:5px;margin:5px;background-color:#d3d3d3;color:#673ab7;border-color:#673ab7}.live-feed-block[_ngcontent-%COMP%]   .bottom-row-feed-settings-live[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]:active{background-color:#673ab7;color:#fff}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]{margin-left:auto;margin-right:auto;max-width:80vw;display:inline-flex}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   #livestream-toggle[_ngcontent-%COMP%]{width:100%}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]{margin:5px;padding:10px;background-color:#a9a9a9;border:1px solid #ccc;width:75%;display:flex;flex-wrap:wrap}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .top-row-feed-settings[_ngcontent-%COMP%], .live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]{width:100%;display:flex;margin-bottom:10px}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .top-row-feed-settings[_ngcontent-%COMP%]   mat-form-field[_ngcontent-%COMP%], .live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   mat-form-field[_ngcontent-%COMP%]{width:100%;height:50px}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .top-row-feed-settings[_ngcontent-%COMP%]   mat-form-field[_ngcontent-%COMP%]   mat-label[_ngcontent-%COMP%], .live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   mat-form-field[_ngcontent-%COMP%]   mat-label[_ngcontent-%COMP%]{color:#000;font-size:18px}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]{display:inline-flex}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   .bottom-row-right-feed-settings[_ngcontent-%COMP%]{width:50%}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   .bottom-row-right-feed-settings[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]{width:100%}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   .bottom-row-right-feed-settings[_ngcontent-%COMP%]   .bottom-row-right-bottom-feed-settings[_ngcontent-%COMP%]{display:flex;width:100%;margin-top:20px}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   .bottom-row-right-feed-settings[_ngcontent-%COMP%]   .bottom-row-right-bottom-feed-settings[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]{width:100%;padding:5px;margin:5px;background-color:#d3d3d3;color:#673ab7;border-color:#673ab7}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   .bottom-row-right-feed-settings[_ngcontent-%COMP%]   .bottom-row-right-bottom-feed-settings[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]:active{background-color:#673ab7;color:#fff}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   .bottom-row-left-feed-settings[_ngcontent-%COMP%]{width:50%}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   .bottom-row-left-feed-settings[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]{width:100%}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   .bottom-row-left-feed-settings[_ngcontent-%COMP%]   .bottom-row-left-bottom-feed-settings[_ngcontent-%COMP%]{display:flex;margin-top:20px}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   .bottom-row-left-feed-settings[_ngcontent-%COMP%]   .bottom-row-left-bottom-feed-settings[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]{width:50%;padding:5px;margin:5px;background-color:#d3d3d3;color:#673ab7;border-color:#673ab7}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   .bottom-row-left-feed-settings[_ngcontent-%COMP%]   .bottom-row-left-bottom-feed-settings[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]:active{background-color:#673ab7;color:#fff}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]{width:50%;padding:5px;margin:5px;background-color:#d3d3d3;color:#673ab7;border-color:#673ab7}.live-feed-block[_ngcontent-%COMP%]   .floating-island[_ngcontent-%COMP%]   .live-feed-settings[_ngcontent-%COMP%]   .bottom-row-feed-settings[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]:active{background-color:#673ab7;color:#fff}.live-feed-block[_ngcontent-%COMP%]   .function-settings[_ngcontent-%COMP%]{margin:5px;padding:10px;background-color:#a9a9a9;border:1px solid #ccc;width:18%;display:flex;flex-direction:column;align-items:center;justify-content:space-between}.live-feed-block[_ngcontent-%COMP%]   .function-settings[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]{width:92%;padding:5px;margin:5px;background-color:#d3d3d3;color:#673ab7;border-color:#673ab7}.live-feed-block[_ngcontent-%COMP%]   .function-settings[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]:active{background-color:#673ab7;color:#fff}.live-feed-block[_ngcontent-%COMP%]   .function-settings[_ngcontent-%COMP%]   mat-form-field[_ngcontent-%COMP%]{width:95%}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]{width:23%;margin:5px;padding:10px;background-color:#a9a9a9;border:1px solid #ccc;display:flex;flex-wrap:wrap}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .manual-row[_ngcontent-%COMP%]{display:flex;flex-direction:row;width:100%}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .camera-settings[_ngcontent-%COMP%]{width:100%;display:flex;flex-wrap:wrap;margin-bottom:10px}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .camera-settings[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{width:100%;margin-bottom:10px}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .camera-settings[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]{width:100%;padding:5px;margin:5px}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .camera-settings[_ngcontent-%COMP%]   mat-form-field[_ngcontent-%COMP%]{width:100%;height:70px}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .camera-settings[_ngcontent-%COMP%]   mat-form-field[_ngcontent-%COMP%]   mat-label[_ngcontent-%COMP%]{color:#000;font-size:18px}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .camera-settings[_ngcontent-%COMP%]   .avi-div[_ngcontent-%COMP%]{width:98%;display:inline-flex}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .camera-settings[_ngcontent-%COMP%]   .avi-div[_ngcontent-%COMP%]   p[_ngcontent-%COMP%]{width:20%}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .camera-settings[_ngcontent-%COMP%]   .avi-div[_ngcontent-%COMP%]   mat-button-toggle-group[_ngcontent-%COMP%]{width:80%;margin-left:10%;border-color:#673ab7}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .camera-settings[_ngcontent-%COMP%]   .avi-div[_ngcontent-%COMP%]   mat-button-toggle-group[_ngcontent-%COMP%]   mat-button-toggle[_ngcontent-%COMP%]{width:100%;background-color:#d3d3d3;color:#673ab7;border-color:#673ab7}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .camera-settings[_ngcontent-%COMP%]   .avi-div[_ngcontent-%COMP%]   mat-button-toggle-group[_ngcontent-%COMP%]   .mat-button-toggle-checked[_ngcontent-%COMP%]{background-color:#673ab7;color:#fff}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .toggle_button[_ngcontent-%COMP%]{width:100%;padding:5px;margin:5px;background-color:#d3d3d3;color:#673ab7;border-color:#673ab7;text-wrap:pretty}.live-feed-block[_ngcontent-%COMP%]   .recording-settings[_ngcontent-%COMP%]   .toggle_button[_ngcontent-%COMP%]:active{background-color:#673ab7;color:#fff}.hist-feed[_ngcontent-%COMP%]{display:inline-block;margin:5px;border:1px solid #ccc}.hist-feed[_ngcontent-%COMP%]   img[_ngcontent-%COMP%]{width:100%}#hist_max[_ngcontent-%COMP%]{display:block;position:relative;right:-92%;top:2%;color:#d3d3d3;font-weight:600;font-size:14pt}",
              ],
            })),
            n
          );
        })(),
        kU = (() => {
          class n {
            constructor() {
              this.title = "wormspy";
            }
          }
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵcmp = Dn({
              type: n,
              selectors: [["app-root"]],
              decls: 2,
              vars: 0,
              template: function (t, i) {
                1 & t && (Me(0, "app-live-feed"), Me(1, "router-outlet"));
              },
              directives: [xU, ap],
              styles: [""],
            })),
            n
          );
        })(),
        FU = (() => {
          class n {}
          return (
            (n.ɵfac = function (t) {
              return new (t || n)();
            }),
            (n.ɵmod = he({ type: n, bootstrap: [kU] })),
            (n.ɵinj = ce({
              providers: [],
              imports: [[gC, pH, eB, TV, Mc, DU, mU, TH, dN, uN]],
            })),
            n
          );
        })();
      (function SF() {
        Db = !1;
      })(),
        qP()
          .bootstrapModule(FU)
          .catch((n) => console.error(n));
    },
  },
  (ae) => {
    ae((ae.s = 233));
  },
]);
