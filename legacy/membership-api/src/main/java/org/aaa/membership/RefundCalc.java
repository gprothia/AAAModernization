package org.aaa.membership;

import java.util.Date;
import java.util.Properties;
import java.util.concurrent.TimeUnit;

/** Cancellation refunds: the unused part of the year, pro rata. Added 2017. */
public class RefundCalc {

    private final Properties config = Config.load();

    /** Whole dollars to refund when the member cancels on {@code today}. */
    public int refund(Member m, Date today) {
        long msLeft = m.expires.getTime() - today.getTime();
        long daysLeft = TimeUnit.MILLISECONDS.toDays(msLeft);

        int cutoff = Integer.parseInt(config.getProperty("refund.cutoff.days"));
        if (daysLeft <= cutoff) {
            return 0;                                      // too close to expiry: no refund
        }

        double perDay = m.paid.doubleValue() / 365;        // 365 even in a leap year
        return (int) Math.floor(perDay * daysLeft);        // always rounded down to whole dollars
    }
}
