// Package submit implements submitting transactions to Horizon.
package submit

import (
	"net/http"
	"time"

	"github.com/go-kit/kit/log"
	"github.com/go-kit/kit/log/level"
	"github.com/kinecosystem/go/build"
	"github.com/kinecosystem/go/clients/horizon"

	"github.com/kinecosystem/core/pkg/errors"
)

const (
	submitTimeout       = 20 * time.Second
	retryFailedTxAmount = 10
)

func SubmitWithRetry(horizonAddr string, network build.Network, ops []build.TransactionMutator, seed string, logger log.Logger) error {
	var err error
	for i := 0; i < retryFailedTxAmount; i++ {
		level.Info(logger).Log("retry_index", i, "msg", "submitting transaction")

		client := horizon.Client{
			URL:  horizonAddr,
			HTTP: &http.Client{Timeout: submitTimeout}}

		fullOps := append(
			[]build.TransactionMutator{
				build.SourceAccount{AddressOrSeed: seed},
				network,
				build.AutoSequence{
					SequenceProvider: &horizon.Client{
						URL:  horizonAddr,
						HTTP: client.HTTP,
					},
				},
			},
			ops...,
		)

		txBuilder, err := build.Transaction(fullOps...)
		if err != nil {
			level.Error(logger).Log("msg", err)
			return err
		}

		txEnv, err := txBuilder.Sign(seed)
		if err != nil {
			level.Error(logger).Log("msg", err)
			return err
		}

		var txEnvB64 string
		txEnvB64, err = txEnv.Base64()
		if err != nil {
			level.Error(logger).Log("msg", err)
			return err
		}

		_, err = client.SubmitTransaction(txEnvB64)
		if err == nil {
			return nil
		}

		errors.GetTxErrorResultCodes(err, logger)

		time.Sleep(5 * time.Second)
	}

	return err
}
