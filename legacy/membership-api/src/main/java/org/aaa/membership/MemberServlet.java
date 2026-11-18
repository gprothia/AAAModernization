package org.aaa.membership;

import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Base64;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import org.apache.log4j.Logger;
import org.json.JSONObject;

/**
 * Member services API. Written 2011, extended 2014 (autopay) and 2017 (cancellations).
 * One servlet handles every path; the action is taken from the URL.
 */
public class MemberServlet extends HttpServlet {

    private static final Logger LOG = Logger.getLogger(MemberServlet.class);
    private static final SimpleDateFormat US_DATE = new SimpleDateFormat("MM/dd/yyyy");

    private final MemberDao dao = new MemberDao();
    private final RenewalService renewals = new RenewalService();
    private final RefundCalc refunds = new RefundCalc();

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        User user = authenticate(req, resp);
        if (user == null) return;

        String id = req.getParameter("id");
        if (!user.canSee(id)) {
            resp.setStatus(403);
            write(resp, new JSONObject().put("error", "Not allowed"));
            return;
        }
        Member m = dao.find(id);
        if (m == null) {
            write(resp, new JSONObject().put("error", "Member not found"));   // still HTTP 200
            return;
        }
        LOG.info("getMember id=" + id + " name=" + m.name + " phone=" + m.phone + " by " + user.name);
        write(resp, toJson(m));
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        User user = authenticate(req, resp);
        if (user == null) return;

        String id = req.getParameter("id");
        if (!user.canSee(id)) {
            resp.setStatus(403);
            write(resp, new JSONObject().put("error", "Not allowed"));
            return;
        }
        Member m = dao.find(id);
        if (m == null) {
            write(resp, new JSONObject().put("error", "Member not found"));
            return;
        }

        if (req.getRequestURI().endsWith("/renewMember")) {
            boolean autopay = "true".equals(req.getParameter("autopay"));
            RenewalService.Result r = renewals.renew(m, autopay);
            dao.saveRenewal(m.id, r.newExpiry, r.charged);
            LOG.info("renewMember id=" + id + " charged=" + r.charged + " card=" + req.getParameter("card"));
            write(resp, new JSONObject().put("memberId", m.id)
                    .put("expires", US_DATE.format(r.newExpiry)).put("charged", r.charged));
            return;
        }

        if (req.getRequestURI().endsWith("/cancelMember")) {
            // Agents may cancel any member and refund any amount. Members may cancel their own.
            int refund = refunds.refund(m, new java.util.Date());
            dao.saveCancellation(m.id, refund);          // no check for an earlier cancellation
            LOG.info("cancelMember id=" + id + " refund=" + refund + " phone=" + m.phone);
            write(resp, new JSONObject().put("memberId", m.id).put("refund", refund));
            return;
        }

        resp.setStatus(404);
    }

    /** HTTP Basic against the users table. Missing or wrong credentials: 401. */
    private User authenticate(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String header = req.getHeader("Authorization");
        if (header != null && header.startsWith("Basic ")) {
            String[] parts = new String(Base64.getDecoder().decode(header.substring(6))).split(":", 2);
            User u = dao.login(parts[0], parts.length > 1 ? parts[1] : "");
            if (u != null) return u;
        }
        resp.setHeader("WWW-Authenticate", "Basic realm=\"members\"");
        resp.sendError(401);
        return null;
    }

    private JSONObject toJson(Member m) {
        return new JSONObject().put("memberId", m.id).put("name", m.name).put("phone", m.phone)
                .put("plan", m.plan).put("status", m.status)
                .put("expires", US_DATE.format(m.expires)).put("paid", m.paid);
    }

    private void write(HttpServletResponse resp, JSONObject body) throws IOException {
        resp.setContentType("application/json");
        resp.getWriter().write(body.toString());
    }
}
